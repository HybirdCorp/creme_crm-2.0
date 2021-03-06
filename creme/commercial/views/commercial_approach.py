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

# from creme.creme_core.auth.decorators import login_required
# from creme.creme_core.views.generic import add_to_entity
from creme.creme_core.views.generic.add import AddingInstanceToEntityPopup

from ..forms.commercial_approach import ComAppCreateForm
from ..models import CommercialApproach


# @login_required
# def add(request, entity_id):
#     return add_to_entity(request, entity_id, ComAppCreateForm,
#                          _('New commercial approach for «%s»'),
#                          submit_label=_('Save the commercial approach'),
#                         )
class CommercialApproachCreation(AddingInstanceToEntityPopup):
    model = CommercialApproach
    form_class = ComAppCreateForm
    title = _('New commercial approach for «{entity}»')
