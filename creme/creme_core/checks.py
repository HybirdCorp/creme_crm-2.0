# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2015-2018  Hybird
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

from django.apps import apps
from django.conf import settings
from django.core.checks import register, Error, Warning, Tags as CoreTags
from django.db.utils import DatabaseError

# from .models import CremeEntity


class Tags:
    settings = 'settings'
    api_breaking = 'api_breaking'
    deprecation = 'deprecation'


@register(Tags.settings)
def check_secret_key(**kwargs):
    errors = []

    if settings.SECRET_KEY == '1&7rbnl7u#+j-2#@5=7@Z0^9v@y_Q!*y^krWS)r)39^M)9(+6(':
        errors.append(Error("You did not generate a secret key.",
                            hint='Change the SECRET_KEY setting in your'
                                 ' local_settings.py/project_settings.py\n'
                                 'Use the result of the command "python manage.py build_secret_key".',
                            obj='creme.creme_core',
                            id='creme.E002',
                           )
                     )

    return errors


def check_uninstalled_apps(**kwargs):
    """Check the badly uninstalled apps.
    BEWARE: it crashes if the ContentType table does not exist (first migration).
    """
    warnings = []

    if settings.TESTS_ON:
        return warnings

    try:
        app_labels = list(apps.get_model('contenttypes.ContentType')
                              .objects
                              .order_by('app_label')
                              .distinct()
                              .values_list('app_label', flat=True)
                         )
    except DatabaseError:
        pass
    else:
        for app_label in app_labels:
            try:
                apps.get_app_config(app_label)
            except LookupError:
                warnings.append(
                    Warning(
                        'The app seems not been correctly uninstalled.',
                        hint="""If it's a Creme app, uninstall it with the command "creme_uninstall" """
                             """(you must enable this app in your settings before).""",
                        obj=app_label,
                        id='creme.E003',
                    )
                )

    return warnings


@register(CoreTags.models)
def check_entity_ordering(**kwargs):
    from .models import CremeEntity

    errors = []

    for model in apps.get_models():
        if not issubclass(model, CremeEntity):
            continue

        ordering = model._meta.ordering

        if not ordering or (len(ordering) == 1 and 'id' in ordering[0]):
            errors.append(
                Error(
                    '"{}" should have a Meta.ordering different from "id" '
                    'like all CremeEntities'.format(model),
                    hint='Change the "ordering" attribute in the Meta class of your model.',
                    obj='creme.creme_core',
                    id='creme.E005',
               )
            )

    return errors


# NB: E007
@register(CoreTags.models)
def check_real_entity_foreign_keys(**kwargs):
    from .models.fields import RealEntityForeignKey

    errors = []

    for model in apps.get_models():
        for field in vars(model).values():
            if isinstance(field, RealEntityForeignKey):
                errors.extend(field.check())

    return errors


@register(CoreTags.urls)
def check_swapped_urls(**kwargs):
    from django.urls import reverse, NoReverseMatch

    from creme.creme_core.conf.urls import swap_manager

    errors = []

    for group in swap_manager:
        for swapped in group.swapped():
            name = swapped.pattern.name

            try:
                reverse(viewname=name, args=swapped.check_args)
            except NoReverseMatch:
                errors.append(
                    Error(
                        'The URL "{url}" (args={args}) has been swapped from the app '
                        '"{app}" but never defined.'.format(
                            url=name,
                            args=swapped.verbose_args,
                            app=group.app_name,
                        ),
                        hint='Define this URL in the file "urls.py" of the module '
                             'which defines the concrete model.',
                        obj='creme.creme_core',
                        id='creme.E008',
                    )
                )

    return errors
