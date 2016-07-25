"""Models for the programs app."""
# pylint: disable=model-missing-unicode,no-member
from uuid import uuid4

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from solo.models import SingletonModel

from programs.apps.programs import constants
from programs.apps.programs.fields import ResizingImageField


RESIZABLE_IMAGE_SIZES = [(1440, 480), (726, 242), (435, 145), (348, 116)]


def _choices(*values):
    """
    Helper for use with model field 'choices'.
    """
    return [(value, ) * 2 for value in values]


class Program(TimeStampedModel):
    """
    Representation of a Program.
    """

    uuid = models.UUIDField(
        blank=True,
        default=uuid4,
        editable=False,
        unique=True,
    )

    name = models.CharField(
        help_text=_('The user-facing display name for this Program.'),
        max_length=255,
        unique=True,
    )

    subtitle = models.CharField(
        help_text=_('A brief, descriptive subtitle for the Program.'),
        max_length=255,
        blank=True,
    )

    # TODO: Replace with ForeignKey to ProgramCategory model.
    category = models.CharField(
        help_text=_('The category / type of Program.'),
        max_length=32,
        choices=_choices(
            constants.ProgramCategory.XSERIES,
            constants.ProgramCategory.MICROMASTERS,
        ),
    )

    status = models.CharField(
        help_text=_('The lifecycle status of this Program.'),
        max_length=24,
        choices=_choices(
            constants.ProgramStatus.UNPUBLISHED,
            constants.ProgramStatus.ACTIVE,
            constants.ProgramStatus.RETIRED,
            constants.ProgramStatus.DELETED,
        ),
        default=constants.ProgramStatus.UNPUBLISHED,
        # though this field is not nullable, setting blank=True ensures validators
        # will reject the empty string, instead of implicitly replacing it with the
        # default value.  This is consistent with how None/null is handled.
        blank=True,
    )

    marketing_slug = models.CharField(
        help_text=_('Slug used to generate links to the marketing site'),
        blank=True,
        max_length=255
    )

    banner_image = ResizingImageField(
        path_template='program/banner/{uuid}',
        sizes=RESIZABLE_IMAGE_SIZES,
        null=True,
        blank=True,
        max_length=1000,
    )

    def save(self, *a, **kw):
        """
        Verify that the marketing slug is not empty if the user has attempted
        to activate an XSeries.
        """
        if self.category == constants.ProgramCategory.XSERIES and self.status == constants.ProgramStatus.ACTIVE:
            if not self.marketing_slug:
                raise ValidationError(_(
                    "Active XSeries Programs must have a valid marketing slug."
                ))

        return super(Program, self).save(*a, **kw)

    class Meta(object):  # pylint: disable=missing-docstring
        index_together = ('status', 'category')

    def __unicode__(self):
        return unicode(self.name)


class Organization(TimeStampedModel):
    """
    Represents the organization offering one or more courses and/or
    programs.  At present, Studio (edx-platform) hosts the source of
    truth for this data; a minimal subset of that data is replicated
    into this system in order to enforce referential integrity internally.
    """
    key = models.CharField(
        help_text=_('The string value of an org key identifying this organization in the LMS.'),
        unique=True,
        max_length=64,
        db_index=True,
    )
    display_name = models.CharField(
        help_text=_('The display name of this organization.'),
        max_length=128,
    )
    programs = models.ManyToManyField(Program, related_name='organizations', through='ProgramOrganization')

    def __unicode__(self):
        return unicode(self.display_name)


class ProgramOrganization(TimeStampedModel):
    """
    This is a m2m table that would otherwise be automatically generated by django's ORM.
    By defining it explicity here, we can use TimeStampedModel, and have an easier path
    to further accessing or customizing the model's data / methods as needed.
    """
    program = models.ForeignKey(Program)
    organization = models.ForeignKey(Organization)

    # TODO: we may need validation to ensure that you cannot remove a program's
    # org association if the program contains course codes that are associated
    # with that org.
    def save(self, *a, **kw):
        """
        Prevent more than one org from being associated with a program.
        This is a temporary, application-level constraint.
        """
        if not self.id:  # pylint: disable=no-member
            # Before creating, check program is not already associated with some organization
            if ProgramOrganization.objects.filter(program=self.program).exists():
                raise ValidationError(_('Cannot associate multiple organizations with a program.'))

        return super(ProgramOrganization, self).save(*a, **kw)


class CourseCode(TimeStampedModel):
    """
    Represents a course independent of run / mode.  This is used to link
    multiple runs / modes of the same course offering within a program,
    both for purposes of presentation and in order to enforce logic
    associated with program completion (i.e. one completed run for each
    course code in the program indicates completion of the program).
    """
    organization = models.ForeignKey(Organization)
    key = models.CharField(
        help_text=_(
            "The 'course' part of course_keys associated with this course code, "
            "for example 'DemoX' in 'edX/DemoX/Demo_Course'."
        ),
        max_length=64,
    )
    display_name = models.CharField(
        help_text=_('The display name of this course code.'),
        max_length=128,
    )
    programs = models.ManyToManyField(Program, related_name='course_codes', through='ProgramCourseCode')

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = ('organization', 'key')

    def __unicode__(self):
        return unicode(self.display_name)


class ProgramCourseCode(TimeStampedModel):
    """
    Represents the many-to-many association of a course code with a program.
    """
    program = models.ForeignKey(Program)
    course_code = models.ForeignKey(CourseCode)
    position = models.IntegerField()

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = ('program', 'position')
        ordering = ['position']

    def __unicode__(self):
        return unicode(self.course_code)

    def save(self, *a, **kw):
        """
        Override save() to validate m2m cardinality and automatically set the position for a new row.
        """
        if self.position is None:
            # before creating, ensure that the program has an association with the same org as this course code
            if not ProgramOrganization.objects.filter(
                    program=self.program, organization=self.course_code.organization).exists():
                raise ValidationError(_('Course code must be offered by the same organization offering the program.'))
            # automatically set position attribute for a new row
            res = ProgramCourseCode.objects.filter(program=self.program).aggregate(max_position=models.Max('position'))
            self.position = (res['max_position'] or 0) + 1
        return super(ProgramCourseCode, self).save(*a, **kw)


class ProgramCourseRunMode(TimeStampedModel):
    """
    Represents a specific run and mode of a course in a specific LMS, within the context of a program.
    """
    program_course_code = models.ForeignKey(ProgramCourseCode, related_name='run_modes')
    lms_url = models.CharField(
        help_text=_("The URL of the LMS where this course run / mode is being offered."),
        max_length=1024,
        blank=True,
    )
    course_key = models.CharField(
        help_text=_("A string referencing the course key identifying this run / mode in the target LMS."),
        max_length=255,
    )
    mode_slug = models.CharField(
        help_text=_("The mode_slug value which uniquely identifies the mode in the target LMS."),
        max_length=64,
    )
    sku = models.CharField(
        help_text=_("The sku associated with this run/mode in the ecommerce system working with the target LMS."),
        max_length=255,
        blank=True,
    )

    start_date = models.DateTimeField(
        help_text=_("The start date of this course run in the target LMS.")
    )

    run_key = models.CharField(
        help_text=_("A string referencing the last part of course key identifying this course run in the target LMS."),
        max_length=255
    )

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = (('program_course_code', 'course_key', 'mode_slug', 'sku'))

    def save(self, *_a, **__kw):
        """
        The unique_together constraint only gives us free validation when using
        Django's ModelForm. Attempts to directly save a model object violating
        this constraint will raise an IntegrityError. That being the case, the
        constraint is manually enforced here. Attempts to violate it will be met
        with a ValidationError.
        """

        # TODO (jsa): I'm now convinced that multiple table inheritance is better
        # - one table without SKUs and one table with NOT NULL / UNIQUE SKUs.
        # This compromise should suffice initially.

        if ProgramCourseRunMode.objects.filter(
                program_course_code=self.program_course_code,
                course_key=self.course_key,
                mode_slug=self.mode_slug,
                sku=self.sku,
        ).exclude(id=self.id).exists():  # pylint: disable=no-member
            raise ValidationError(_('Duplicate course run modes are not allowed for course codes in a program.'))

        try:
            course_key = CourseKey.from_string(self.course_key)
            self.run_key = course_key.run
        except InvalidKeyError:
            raise ValidationError(_("Invalid course key."))

        return super(ProgramCourseRunMode, self).save()


class ProgramDefault(SingletonModel):
    """
    Model used to store default program configuration.
    This includes a default, resizable banner image which is
    used if a given program has not specified its own banner image.
    This model is a singleton - only one instance exists.
    """
    banner_image = ResizingImageField(
        path_template='program/banner/default',
        sizes=RESIZABLE_IMAGE_SIZES,
        null=True,
        blank=True,
        max_length=1000,
    )
