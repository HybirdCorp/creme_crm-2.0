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

from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from creme.creme_core.gui.button_menu import Button

from . import get_act_model
from .constants import REL_SUB_COMPLETE_GOAL


class CompleteGoalButton(Button):
    id_           = Button.generate_id('commercial', 'complete_goal')
    verbose_name  = _(u'Completes a goal (Commercial action)')
    # template_name = 'commercial/templatetags/button_complete_goal.html'
    template_name = 'commercial/buttons/complete-goal.html'
    permission    = 'commercial'

    def render(self, context):
        context['predicate_id'] = REL_SUB_COMPLETE_GOAL
        context['act_ct'] = ContentType.objects.get_for_model(get_act_model())

        # return super(CompleteGoalButton, self).render(context)
        return super().render(context)


# complete_goal_button = CompleteGoalButton()
