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

import warnings

# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from creme.creme_core import models as creme_models
from creme.creme_core.models import fields as creme_fields


class ActionManager(models.Manager):
    def filter_by_user(self, user):
        return self.filter(user__in=[user] + user.teams)


class Action(creme_models.CremeModel):
    title             = models.CharField(_('Title'), max_length=200)
    is_ok             = models.BooleanField(_('Expected reaction has been done'), editable=False, default=False)
    description       = models.TextField(_('Source action'), blank=True)
    creation_date     = creme_fields.CreationDateTimeField(_('Creation date'), editable=False)
    expected_reaction = models.TextField(_('Target action'), blank=True)
    deadline          = models.DateTimeField(_('Deadline'))
    validation_date   = models.DateTimeField(_('Validation date'), blank=True, null=True, editable=False)
    user              = creme_fields.CremeUserForeignKey(verbose_name=_('Owner user'))

    # entity_content_type = models.ForeignKey(ContentType, related_name='action_entity_set', editable=False, on_delete=models.CASCADE)
    # entity_id           = models.PositiveIntegerField(editable=False).set_tags(viewable=False)
    # creme_entity        = GenericForeignKey(ct_field="entity_content_type", fk_field='entity_id')
    entity_content_type = creme_fields.EntityCTypeForeignKey(related_name='+', editable=False)
    entity              = models.ForeignKey(creme_models.CremeEntity, related_name='assistants_actions',
                                            editable=False, on_delete=models.CASCADE,
                                           ).set_tags(viewable=False)
    creme_entity        = creme_fields.RealEntityForeignKey(ct_field='entity_content_type', fk_field='entity')

    objects = ActionManager()

    creation_label = _('Create an action')
    save_label     = _('Save the action')

    class Meta:
        app_label = 'assistants'
        verbose_name = _('Action')
        verbose_name_plural = _('Actions')

    def __str__(self):
        return self.title

    def get_edit_absolute_url(self):
        return reverse('assistants__edit_action', args=(self.id,))

    @staticmethod
    def get_actions_it(entity, today):
        warnings.warn('Action.get_actions_it() is deprecated.', DeprecationWarning)
        return Action.objects.filter(entity_id=entity.id, is_ok=False, deadline__gt=today) \
                             .select_related('user')

    @staticmethod
    def get_actions_nit(entity, today):
        warnings.warn('Action.get_actions_nit() is deprecated.', DeprecationWarning)
        return Action.objects.filter(entity_id=entity.id, is_ok=False, deadline__lte=today) \
                             .select_related('user')

    @staticmethod
    def get_actions_it_for_home(user, today):
        warnings.warn('Action.get_actions_it_for_home() is deprecated.', DeprecationWarning)
        return Action.objects.filter(is_ok=False,
                                     deadline__gt=today,
                                     user__in=[user] + user.teams,
                                     # entity__is_deleted=False,
                                    ) \
                             .select_related('user')

    @staticmethod
    def get_actions_nit_for_home(user, today):
        warnings.warn('Action.get_actions_nit_for_home() is deprecated.', DeprecationWarning)
        return Action.objects.filter(is_ok=False,
                                     deadline__lte=today,
                                     user__in=[user] + user.teams,
                                     # entity__is_deleted=False,
                                    ) \
                             .select_related('user')

    @staticmethod
    def get_actions_it_for_ctypes(ct_ids, user, today):
        warnings.warn('Action.get_actions_it_for_ctypes() is deprecated.', DeprecationWarning)
        return Action.objects.filter(entity_content_type__in=ct_ids,
                                     user__in=[user] + user.teams,
                                     is_ok=False,
                                     deadline__gt=today,
                                    ) \
                             .select_related('user')

    @staticmethod
    def get_actions_nit_for_ctypes(ct_ids, user, today):
        warnings.warn('Action.get_actions_nit_for_ctypes() is deprecated.', DeprecationWarning)
        return Action.objects.filter(entity_content_type__in=ct_ids,
                                     user__in=[user] + user.teams,
                                     is_ok=False,
                                     deadline__lte=today
                                    ) \
                             .select_related('user')

    def get_related_entity(self):  # For generic views
        return self.creme_entity
