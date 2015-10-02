"""
Mixins for Programs API tests.
"""
from time import time

from django.conf import settings
import jwt


JWT_AUTH = 'JWT_AUTH'


class JwtMixin(object):
    """ Mixin with JWT-related helper functions. """

    JWT_SECRET_KEY = getattr(settings, JWT_AUTH)['JWT_SECRET_KEY']
    JWT_ISSUER = getattr(settings, JWT_AUTH)['JWT_ISSUER']
    JWT_AUDIENCE = getattr(settings, JWT_AUTH)['JWT_AUDIENCE']

    def generate_token(self, payload, secret=None):
        """Generate a JWT token with the provided payload."""
        secret = secret or self.JWT_SECRET_KEY
        token = jwt.encode(payload, secret)
        return token

    def generate_id_token(self, user, admin=False, ttl=0):
        """Generate a JWT id_token that looks like the ones currently
        returned by the edx oidc provider."""

        now = int(time())

        return self.generate_token({
            "iss": self.JWT_ISSUER,
            "sub": user.pk,
            "aud": self.JWT_AUDIENCE,
            "nonce": "dummy-nonce",
            "exp": now + ttl,
            "iat": now,
            "preferred_username": user.username,
            "administrator": admin,
            "email": user.email,
            "locale": "en",
            "name": user.full_name,
            "given_name": "",
            "family_name": "",
        })
