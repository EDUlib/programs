define([
        'jquery',
        'js/models/program_model',
        'js/views/program_details_view'
    ],
    function( $, ProgramModel, ProgramDetailsView ) {
        'use strict';

        describe('ProgramDetailsView', function () {
            var view = {},
                model = {},
                programData = {
                    category: 'xseries',
                    course_codes: [{
                        display_name: 'test-course-display_name',
                        key: 'test-course-key',
                        organization: {
                            display_name: 'test-org-display_name',
                            key: 'test-org-key'
                        },
                        run_modes: [
                            {
                                course_key: 'course-v1:edX+DemoX+Demo_Course',
                                mode_slug: 'honor',
                                sku: null,
                                start_date: 'May 23, 2015'
                            }, {
                                course_key: 'course-v1:edX+DemoX+Demo_Course',
                                mode_slug: 'honor',
                                sku: null,
                                start_date: 'August 01, 2015'
                            }, {
                                course_key: 'course-v1:edX+DemoX+Demo_Course',
                                mode_slug: 'honor',
                                sku: null,
                                start_date: 'December 11, 2015'
                            }
                        ]
                    }],
                    created: '2015-10-20T18:11:46.854451Z',
                    id: 5,
                    marketing_slug: 'test-program-slug',
                    modified: '2015-10-20T18:11:46.854735Z',
                    name: 'test-program-5',
                    organizations: [{
                        display_name: 'test-org-display_name',
                        key: 'test-org-key'
                    }],
                    status: 'unpublished',
                    subtitle: 'test-subtitle'
                },
                testTimeoutInterval = 100,
                errorClass = 'has-error',
                editField = function( el, str ) {
                    var $input = view.$el.find( el ),
                        $btn = $input.next( '.js-enable-edit' );

                    expect( document.activeElement ).not.toEqual( $input[0] );
                    expect( $input ).not.toHaveClass( 'edit' );
                    expect( $input ).toHaveClass( 'is-hidden' );

                    $btn.click();

                    $input.val( str );

                    // Enable editing
                    expect( $input ).not.toHaveClass( 'is-hidden' );
                    expect( $input ).toHaveClass( 'edit' );
                },
                testUnchangedFieldBlur = function( el ) {
                    var $input = view.$el.find( el ),
                        $btn = view.$el.find( '.js-add-course' ),
                        title = $input.val(),
                        update = title;

                    editField( el, update );
                    $btn.focus();
                    $input.blur();

                    expect( title ).toEqual( update );
                    expect( view.model.save ).not.toHaveBeenCalled();
                },
                testUpdatedFieldBlur = function( el, update ) {
                    var $input = view.$el.find( el ),
                        $btn = view.$el.find( '.js-add-course' );

                    expect( $input.val() ).not.toEqual( update );

                    editField( el, update );

                    $btn.focus();
                    $input.blur();

                    expect( $input.val() ).toEqual( update );
                    expect( view.model.save ).toHaveBeenCalled();
                },
                testInvalidUpdate = function( el, update ) {
                    var $input = view.$el.find( el ),
                        $btn = view.$el.find( '.js-add-course' );

                    editField( el, update );

                    $btn.focus();
                    $input.blur();

                    expect( $input ).toHaveClass( errorClass );
                    expect( view.model.save ).not.toHaveBeenCalled();
                };

            beforeEach( function() {
                // Set the DOM
                setFixtures( '<div class="js-program-admin"></div>' );

                jasmine.clock().install();

                spyOn( ProgramModel.prototype, 'save' );

                model = new ProgramModel();
                model.set( programData );

                view = new ProgramDetailsView({
                    model: model
                });
            });

            afterEach( function() {
                view.undelegateEvents();
                view.remove();

                jasmine.clock().uninstall();
            });

            describe( 'View data', function() {
                it( 'should exist', function () {
                    expect( view ).toBeDefined();
                });

                it( 'should render all of the run_modes from the model', function () {
                   var $runs = view.$el.find('.js-course-runs'),
                       domLength = $runs.find('.js-remove-run').length,
                       objLength = programData.course_codes[0].run_modes.length;

                    expect( domLength ).toEqual( objLength );
                });
            });

            describe( 'Delete data', function() {
                it( 'should remove a course when the delete button is clicked', function() {
                    var $el = view.$el.find('.js-course-list'),
                        $removeRunBtn = $el.find('.js-remove-course').first(),
                        count = programData.course_codes.length;

                    expect( $el.find('.js-remove-course').length ).toEqual( count );
                    $removeRunBtn.click();

                    setTimeout( function() {
                        expect( $el.find('.js-remove-course').length ).toEqual( count - 1 );
                    }, testTimeoutInterval );

                    jasmine.clock().tick( testTimeoutInterval + 1 );
                });

                it( 'should remove a course run when the delete button is clicked', function() {
                    var $runs = view.$el.find('.js-course-runs'),
                        $removeRunBtn = $runs.find('.js-remove-run').first(),
                        count = programData.course_codes[0].run_modes.length;

                    expect( $runs.find('.js-remove-run').length ).toEqual( count );
                    $removeRunBtn.click();

                    setTimeout( function() {
                        expect( $runs.find('.js-remove-run').length ).toEqual( count - 1 );
                    }, testTimeoutInterval );

                    jasmine.clock().tick( testTimeoutInterval + 1 );
                });
            });

            describe( 'Add data', function() {
                it( 'should add a new course details view on click of the add course button', function() {
                    var $btn = view.$el.find('.js-add-course').first();

                    expect( view.$el.find('.js-course-select').length ).toEqual( 0 );
                    $btn.click();

                    setTimeout( function() {
                        var $select = view.$el.find('.js-course-select');
                        expect( $select.length ).toEqual( 1 );
                    }, testTimeoutInterval );

                    jasmine.clock().tick( testTimeoutInterval + 1 );
                });

                it( 'should set course details on change of the course select', function() {
                    var $btn = view.$el.find('.js-add-course').first();

                    expect( view.$el.find('.course-details').length ).toEqual( 1 );
                    $btn.click();

                    setTimeout( function() {
                        view.$el.find('.js-course-select').val('002').trigger('change');
                    }, testTimeoutInterval );

                    setTimeout( function() {
                        expect( view.$el.find('.course-details').length ).toEqual( 2 );
                    }, testTimeoutInterval * 2 );

                    jasmine.clock().tick( testTimeoutInterval + 1 );
                    jasmine.clock().tick( ( testTimeoutInterval * 2 ) + 1 );
                });
            });

            describe( 'Edit data', function() {
                it( 'should enable a user to edit the name, subtitle and marketing slug fields', function() {
                    editField( '.program-name', 'name' );
                    editField( '.program-subtitle', 'subtitle' );
                    editField( '.program-marketing-slug', 'marketing-slug' );
                });

                it( 'should not send an API call if a user does not change the value of an editable field', function() {
                    testUnchangedFieldBlur( '.program-name' );
                    testUnchangedFieldBlur( '.program-subtitle' );
                    testUnchangedFieldBlur( '.program-marketing-slug' );
                });

                it( 'should send an API call if a user changes the value of an editable field', function() {
                    testUpdatedFieldBlur( '.program-name',  'new-title' );
                    testUpdatedFieldBlur( '.program-subtitle',  'new-subtitle' );
                    testUpdatedFieldBlur( '.program-marketing-slug',  'new-marketing-slug' );
                });

                it( 'should show error messaging if the updated required field is empty', function() {
                    testInvalidUpdate( '.program-name',  '' );
                });

                it( 'should show error messaging if the updated field value is too long', function() {
                    var chars65 = 'x'.repeat(65),
                        chars256 = 'x'.repeat(256);

                    testInvalidUpdate( '.program-name',  chars65 );
                    testInvalidUpdate( '.program-subtitle',  chars256 );
                    testInvalidUpdate( '.program-marketing-slug',  chars256 );
                });
            });
        });
    }
);