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

from collections import defaultdict
# import warnings

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.gui.bricks import QuerysetBrick

from .models import Action, Alert, Memo, ToDo, UserMessage


class _AssistantsBrick(QuerysetBrick):
    # TODO: move to a method in RealEntityForeignKey ? (like GenericForeignKey.get_prefetch_queryset() ?)
    @staticmethod
    def _populate_related_real_entities(assistants):
        assistants = [assistant for assistant in assistants if assistant.entity_id]
        entities_ids_by_ct = defaultdict(set)

        for assistant in assistants:
            entities_ids_by_ct[assistant.entity_content_type_id].add(assistant.entity_id)

        entities_map = {}
        get_ct = ContentType.objects.get_for_id

        for ct_id, entities_ids in entities_ids_by_ct.items():
            entities_map.update(get_ct(ct_id).model_class().objects.in_bulk(entities_ids))

        for assistant in assistants:
            assistant.creme_entity = entities_map[assistant.entity_id]

    def _get_queryset_for_detailview(self, entity, context):
        """OVERLOAD ME"""
        pass

    def _get_queryset_for_home(self, context):
        """OVERLOAD ME"""
        pass

    # def _get_queryset_for_portal(self, ct_ids, context):
    #     """OVERLOAD ME"""
    #     warnings.warn('assistants.bricks._AssistantsBrick._get_queryset_for_portal() is deprecated.',
    #                   DeprecationWarning
    #                  )

    # @classmethod
    # def _get_contenttype_id(cls):
    #     warnings.warn('assistants.bricks._AssistantsBrick._get_contenttype_id() is deprecated.', DeprecationWarning)
    #
    #     return ContentType.objects.get_for_model(cls.dependencies[0]).id

    def detailview_display(self, context):
        entity = context['object']
        btc = self.get_template_context(
                context, self._get_queryset_for_detailview(entity, context),
        )

        # NB: optimisation ; it avoids the retrieving of the entity during template rendering.
        for assistant in btc['page'].object_list:
            assistant.creme_entity = entity

        return self._render(btc)

    # def portal_display(self, context, ct_ids):
    #     warnings.warn('assistants.bricks._AssistantsBrick.portal_display() is deprecated.', DeprecationWarning)
    #
    #     btc = self.get_template_context(
    #         context, self._get_queryset_for_portal(ct_ids, context),
    #     )
    #     self._populate_related_real_entities(btc['page'].object_list)
    #
    #     return self._render(btc)

    def home_display(self, context):
        btc = self.get_template_context(
                context, self._get_queryset_for_home(context),
        )
        self._populate_related_real_entities(btc['page'].object_list)

        return self._render(btc)


class TodosBrick(_AssistantsBrick):
    id_           = QuerysetBrick.generate_id('assistants', 'todos')
    dependencies  = (ToDo,)
    order_by      = '-creation_date'
    verbose_name  = _('Todos')
    template_name = 'assistants/bricks/todos.html'

    def _get_queryset_for_detailview(self, entity, context):
        # return ToDo.get_todos(entity)
        return ToDo.objects.filter(entity_id=entity.id).select_related('user')

    def _get_queryset_for_home(self, context):
        # return ToDo.get_todos_for_home(context['user'])
        return ToDo.objects.filter_by_user(context['user'])\
                           .filter(entity__is_deleted=False) \
                           .select_related('user')

    # def _get_queryset_for_portal(self, ct_ids, context):
    #     warnings.warn('assistants.bricks.TodosBrick._get_queryset_for_portal() is deprecated.',
    #                   DeprecationWarning
    #                  )
    #     return ToDo.get_todos_for_ctypes(ct_ids, context['user'])


class MemosBrick(_AssistantsBrick):
    id_           = QuerysetBrick.generate_id('assistants', 'memos')
    dependencies  = (Memo,)
    order_by      = '-creation_date'
    verbose_name  = _('Memos')
    template_name = 'assistants/bricks/memos.html'

    def _get_queryset_for_detailview(self, entity, context):
        # return Memo.get_memos(entity)
        return Memo.objects.filter(entity_id=entity.id).select_related('user')

    def _get_queryset_for_home(self, context):
        # return Memo.get_memos_for_home(context['user'])
        return Memo.objects \
                   .filter_by_user(context['user'])\
                   .filter(on_homepage=True, entity__is_deleted=False) \
                   .select_related('user')

    # def _get_queryset_for_portal(self, ct_ids, context):
    #     warnings.warn('assistants.bricks.MemosBrick._get_queryset_for_portal() is deprecated.',
    #                   DeprecationWarning
    #                  )
    #     return Memo.get_memos_for_ctypes(ct_ids, context['user'])


class AlertsBrick(_AssistantsBrick):
    id_           = QuerysetBrick.generate_id('assistants', 'alerts')
    dependencies  = (Alert,)
    order_by      = '-trigger_date'
    verbose_name  = _('Alerts')
    template_name = 'assistants/bricks/alerts.html'

    def _get_queryset_for_detailview(self, entity, context):
        # return Alert.get_alerts(entity)
        return  Alert.objects.filter(is_validated=False, entity_id=entity.id)\
                             .select_related('user')

    def _get_queryset_for_home(self, context):
        # return Alert.get_alerts_for_home(context['user'])
        return Alert.objects.filter_by_user(context['user']) \
                            .filter(is_validated=False,
                                    entity__is_deleted=False,
                                   ) \
                            .select_related('user')

    # def _get_queryset_for_portal(self, ct_ids, context):
    #     warnings.warn('assistants.bricks.AlertsBrick._get_queryset_for_portal() is deprecated.',
    #                   DeprecationWarning
    #                  )
    #     return Alert.get_alerts_for_ctypes(ct_ids, context['user'])


class _ActionsBrick(_AssistantsBrick):
    dependencies  = (Action,)
    order_by      = 'deadline'

    def _get_queryset_for_detailview(self, entity, context):
        return Action.objects \
                     .filter(entity_id=entity.id, is_ok=False) \
                     .select_related('user')

    def _get_queryset_for_home(self, context):
        return Action.objects \
                     .filter_by_user(context['user']) \
                     .filter(is_ok=False, entity__is_deleted=False) \
                     .select_related('user')


# class ActionsOnTimeBrick(_AssistantsBrick):
class ActionsOnTimeBrick(_ActionsBrick):
    id_           = QuerysetBrick.generate_id('assistants', 'actions_it')
    # dependencies  = (Action,)
    # order_by      = 'deadline'
    verbose_name  = _('Actions in time')
    template_name = 'assistants/bricks/actions-on-time.html'

    def _get_queryset_for_detailview(self, entity, context):
        # return Action.get_actions_it(entity, context['today'])
        return super()._get_queryset_for_detailview(entity, context) \
                      .filter(deadline__gt=context['today'])

    def _get_queryset_for_home(self, context):
        # return Action.get_actions_it_for_home(context['user'], context['today'])
        return super()._get_queryset_for_home(context) \
                      .filter(deadline__gt=context['today'])

    # def _get_queryset_for_portal(self, ct_ids, context):
    #     warnings.warn('assistants.bricks.ActionsOnTimeBrick._get_queryset_for_portal() is deprecated.',
    #                   DeprecationWarning
    #                  )
    #     return Action.get_actions_it_for_ctypes(ct_ids, context['user'], context['today'])


# class ActionsNotOnTimeBrick(_AssistantsBrick):
class ActionsNotOnTimeBrick(_ActionsBrick):
    id_           = QuerysetBrick.generate_id('assistants', 'actions_nit')
    # dependencies  = (Action,)
    # order_by      = 'deadline'
    verbose_name  = _('Reactions not in time')
    template_name = 'assistants/bricks/actions-not-on-time.html'

    def _get_queryset_for_detailview(self, entity, context):
        # return Action.get_actions_nit(entity, context['today'])
        return super()._get_queryset_for_detailview(entity, context) \
                      .filter(deadline__lte=context['today'])

    def _get_queryset_for_home(self, context):
        # return Action.get_actions_nit_for_home(context['user'], context['today'])
        return super()._get_queryset_for_home(context) \
                      .filter(deadline__lte=context['today'])

    # def _get_queryset_for_portal(self, ct_ids, context):
    #     warnings.warn('assistants.bricks.ActionsNotOnTimeBrick._get_queryset_for_portal() is deprecated.',
    #                   DeprecationWarning
    #                  )
    #     return Action.get_actions_nit_for_ctypes(ct_ids, context['user'], context['today'])


class UserMessagesBrick(_AssistantsBrick):
    id_           = QuerysetBrick.generate_id('assistants', 'messages')
    dependencies  = (UserMessage,)
    order_by      = '-creation_date'
    verbose_name  = _('User messages')
    template_name = 'assistants/bricks/messages.html'

    def _get_queryset_for_detailview(self, entity, context):
        # return UserMessage.get_messages(entity, context['user'])
        return UserMessage.objects.filter(entity_id=entity.id, recipient=context['user']) \
                          .select_related('sender')

    def _get_queryset_for_home(self, context):
        # return UserMessage.get_messages_for_home(context['user'])
        return UserMessage.objects \
                          .filter(recipient=context['user'], entity__is_deleted=False) \
                          .select_related('sender')

    # def _get_queryset_for_portal(self, ct_ids, context):
    #     warnings.warn('assistants.bricks.UserMessagesBrick._get_queryset_for_portal() is deprecated.',
    #                   DeprecationWarning
    #                  )
    #     return UserMessage.get_messages_for_ctypes(ct_ids, context['user'])
