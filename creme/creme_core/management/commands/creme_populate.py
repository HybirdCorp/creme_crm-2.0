# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from importlib import import_module
import sys
from traceback import format_exception

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.models.signals import pre_save

from creme.creme_core.apps import creme_app_configs
# from creme.creme_core.utils import safe_unicode_error, safe_unicode
from creme.creme_core.utils.collections import OrderedSet
from creme.creme_core.utils.dependence_sort import dependence_sort


def _checked_app_label(app_label, app_labels):
    if app_label not in app_labels:
        raise CommandError('"{}" seems not to be a Creme app '
                           '(see settings.INSTALLED_CREME_APPS)'.format(app_label)
                          )

    return app_label


class BasePopulator:
    dependencies = []  # eg: ['appname1', 'appname2']

    def __init__(self, verbosity, app, all_apps, options, stdout, style):
        self.verbosity = verbosity
        self.app = app
        self.options = options
        self.stdout = stdout
        self.style  = style
        self.build_dependencies(all_apps)

    def __repr__(self):
        return '<Populator({})>'.format(self.app)

    def build_dependencies(self, apps_set):
        deps = []

        for dep in self.dependencies:
            try:
                deps.append(_checked_app_label(dep, apps_set))
            except CommandError as e:
                self.stdout.write('BEWARE: ignored dependencies "{}", {}'.format(dep, e),
                                  self.style.NOTICE,
                                 )

        self.dependencies = deps

    def populate(self):
        raise NotImplementedError

    def get_app(self):
        return self.app

    def get_dependencies(self):
        return self.dependencies


class Command(BaseCommand):
    help = ('Populates the database for the specified applications, or the '
            'entire site if no apps are specified.')
    # args = '[appname ...]'
    leave_locale_alone = True
    requires_migrations_checks = True

    def _signal_handler(self, sender, instance, **kwargs):
        if instance.pk and not isinstance(instance.pk, str):
            # Models with string pk should manage pk manually, so we can optimise
            self.models.add(sender)

    def add_arguments(self, parser):
        parser.add_argument('args', metavar='app_labels', nargs='*',
                            help='Optionally one or more application label.',
                           )

    # def handle(self, *app_names, **options):
    def handle(self, *app_labels, **options):
        verbosity = options.get('verbosity')

        # eg: 'persons', 'creme_core'...
        all_apps = OrderedSet(app_config.label for app_config in creme_app_configs())

        # apps_2_populate = all_apps if not app_names else \
        #                   [_checked_app_label(app, all_apps) for app in app_names]
        apps_2_populate = all_apps if not app_labels else \
                          [_checked_app_label(app, all_apps) for app in app_labels]

        # ----------------------------------------------------------------------
        populators = []
        populators_names = set()  # Names of populators that will be run
        total_deps = set()  # Populators names that are needed by our populators
        total_missing_deps = set()  # All populators names that are added by
                                    # this script because of dependencies

        while True:
            changed = False

            for app_label in apps_2_populate:
                populator = self._get_populator(app_label=app_label, verbosity=verbosity, all_apps=all_apps, options=options)

                if populator is not None:
                    populators.append(populator)
                    populators_names.add(app_label)
                    total_deps.update(populator.dependencies)
                    changed = True

            if not changed: break

            apps_2_populate = total_deps - populators_names
            total_missing_deps |= apps_2_populate

        if total_missing_deps and verbosity >= 1:
            self.stdout.write('Additional dependencies will be populated: {}'.format(
                                    ', '.join(total_missing_deps)
                                ),
                              self.style.NOTICE
                             )

        # Clean the dependencies (avoid dependencies that do not exist in
        # 'populators', which would cause Exception raising)
        for populator in populators:
            populator.build_dependencies(populators_names)

        populators = dependence_sort(populators,
                                     BasePopulator.get_app,
                                     BasePopulator.get_dependencies,
                                    )

        # ----------------------------------------------------------------------
        self.models = set()
        dispatch_uid = 'creme_core-populate_command'

        pre_save.connect(self._signal_handler, dispatch_uid=dispatch_uid)

        for populator in populators:
            if verbosity >= 1:
                self.stdout.write('Populate "{}" ...'.format(populator.app), ending='')
                self.stdout.flush()

            try:
                populator.populate()
            except Exception as e:
                # self.stderr.write(' Populate "{}" failed ({})'.format(populator.app, safe_unicode_error(e)))
                self.stderr.write(' Populate "{}" failed ({})'.format(populator.app, e))
                if verbosity >= 1:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    # self.stderr.write(safe_unicode(''.join(format_exception(exc_type, exc_value, exc_traceback))))
                    self.stderr.write(''.join(format_exception(exc_type, exc_value, exc_traceback)))

            if verbosity >= 1:
                # self.stdout.write(' OK', self.style.MIGRATE_SUCCESS)
                self.stdout.write(' OK', self.style.SUCCESS)

        pre_save.disconnect(dispatch_uid=dispatch_uid)

        # ----------------------------------------------------------------------
        if self.models:
            if verbosity >= 1:
                self.stdout.write('Update sequences for models : {}'.format(
                                        [model.__name__ for model in self.models]
                                    ),
                                  ending='',
                                 )
                self.stdout.flush()

            connection = connections[options.get('database', DEFAULT_DB_ALIAS)]
            cursor = connection.cursor()

            for line in connection.ops.sequence_reset_sql(no_style(), self.models):
                cursor.execute(line)

            # connection.close() #seems useless (& does not work with mysql)

            if verbosity >= 1:
                # self.stdout.write(self.style.MIGRATE_SUCCESS(' OK'))
                self.stdout.write(self.style.SUCCESS(' OK'))
        elif verbosity >= 1:
                self.stdout.write('No sequence to update.')

        if verbosity >= 1:
            # self.stdout.write(self.style.MIGRATE_SUCCESS('Populate is OK.'))
            self.stdout.write(self.style.SUCCESS('Populate is OK.'))

    def _get_populator(self, app_label, verbosity, all_apps, options):
        try:
            mod = import_module(apps.get_app_config(app_label).name + '.populate')
        except ImportError:
            if verbosity >= 1:
                self.stdout.write(self.style.NOTICE('Disable populate for "{}": '
                                                    'it does not have any "populate.py" script.'.format(app_label)
                                                   )
                                 )

            return None

        populator_class = getattr(mod, 'Populator', None)

        if populator_class is None:
            if verbosity >= 1:
                self.stdout.write(self.style.NOTICE('Disable populate for "{}": '
                                                    'its populate.py script has no "Populator" class.'.format(app_label)
                                                   )
                                 )

            return None

        try:
            populator = populator_class(verbosity, app_label, all_apps, options, self.stdout, self.style)
        except Exception as e:
            self.stderr.write('Disable populate for "{}": error when creating populator [{}].'.format(app_label, e))
        else:
            return populator
