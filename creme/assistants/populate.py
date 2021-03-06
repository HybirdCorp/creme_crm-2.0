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

from django.conf import settings

from creme.creme_core.management.commands.creme_populate import BasePopulator
from creme.creme_core.models import SettingValue, Job, BrickDetailviewLocation, BrickHomeLocation
from creme.creme_core.utils import create_if_needed

from .bricks import AlertsBrick, MemosBrick, TodosBrick, UserMessagesBrick
from .constants import PRIO_IMP_PK, USERMESSAGE_PRIORITIES
from .creme_jobs import usermessages_send_type
from .models import UserMessagePriority
from .setting_keys import todo_reminder_key


class Populator(BasePopulator):
    dependencies = ['creme_core']

    def populate(self):
        already_populated = UserMessagePriority.objects.filter(pk=PRIO_IMP_PK).exists()

        for pk, title in USERMESSAGE_PRIORITIES.items():
            create_if_needed(UserMessagePriority, {'pk': pk}, title=str(title), is_custom=False)

        SettingValue.objects.get_or_create(key_id=todo_reminder_key.id, defaults={'value': 9})

        Job.objects.get_or_create(type_id=usermessages_send_type.id,
                                  defaults={'language': settings.LANGUAGE_CODE,
                                            'status':   Job.STATUS_OK,
                                           },
                                 )

        if not already_populated:
            RIGHT = BrickDetailviewLocation.RIGHT
            BrickDetailviewLocation.create_if_needed(brick_id=TodosBrick.id_,        order=100, zone=RIGHT)
            BrickDetailviewLocation.create_if_needed(brick_id=MemosBrick.id_,        order=200, zone=RIGHT)
            BrickDetailviewLocation.create_if_needed(brick_id=AlertsBrick.id_,       order=300, zone=RIGHT)
            BrickDetailviewLocation.create_if_needed(brick_id=UserMessagesBrick.id_, order=400, zone=RIGHT)

            # BlockPortalLocation.create_or_update(brick_id=MemosBrick.id_,        order=100)
            # BlockPortalLocation.create_or_update(brick_id=AlertsBrick.id_,       order=200)
            # BlockPortalLocation.create_or_update(brick_id=UserMessagesBrick.id_, order=300)

            # BlockPortalLocation.create_or_update(app_name='creme_core', brick_id=MemosBrick.id_,        order=100)
            # BlockPortalLocation.create_or_update(app_name='creme_core', brick_id=AlertsBrick.id_,       order=200)
            # BlockPortalLocation.create_or_update(app_name='creme_core', brick_id=UserMessagesBrick.id_, order=300)
            BrickHomeLocation.objects.create(brick_id=MemosBrick.id_,        order=100)
            BrickHomeLocation.objects.create(brick_id=AlertsBrick.id_,       order=200)
            BrickHomeLocation.objects.create(brick_id=UserMessagesBrick.id_, order=300)