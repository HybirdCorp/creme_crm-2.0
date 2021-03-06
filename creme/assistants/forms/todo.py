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

from datetime import datetime, time

from django.forms import TypedChoiceField
from django.utils.timezone import localtime
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.forms import CremeModelWithUserForm
from creme.creme_core.forms.widgets import CalendarWidget
from creme.creme_core.utils.dates import make_aware_dt

from ..models import ToDo


class ToDoForm(CremeModelWithUserForm):
    deadline_hour = TypedChoiceField(label=_(u'Deadline hour'), coerce=int,
                                     choices=[(i, '%ih' % i) for i in range(0, 24)],
                                     required=False, empty_value=None, initial=8,
                                     help_text=_(u'The hour is used only if you set the deadline date.'),
                                    )

    class Meta(CremeModelWithUserForm.Meta):
        model = ToDo
        widgets = {'deadline': CalendarWidget}

    def __init__(self, entity, *args, **kwargs):
        # super(ToDoForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.instance.creme_entity = entity

        deadline = self.instance.deadline
        if deadline:
            self.fields['deadline_hour'].initial = localtime(deadline).hour

    def clean(self):
        # cdata = super(ToDoForm, self).clean()
        cdata = super().clean()

        if not self._errors:
            get_data = cdata.get
            deadline = get_data('deadline')

            if deadline:
                deadline_hour = get_data('deadline_hour') 

                if deadline_hour is None:
                    self.add_error('deadline_hour', _(u'The hour is required if you set a date.'))
                else:
                    cdata['deadline'] = make_aware_dt(datetime.combine(deadline,
                                                                       time(deadline_hour)
                                                                      )
                                                     )

        return cdata
