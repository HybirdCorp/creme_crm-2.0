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

# import warnings
#
# from django.utils.translation import ugettext_lazy as _
#
# from creme.creme_core.views.generic import app_portal
#
# from creme.creme_config.utils import generate_portal_url
#
# from .. import get_event_model
#
#
# def portal(request):
#     warnings.warn('events.views.portal.portal() is deprecated.', DeprecationWarning)
#
#     Event = get_event_model()
#     stats = ((_('Number of events'), Event.objects.count()),
#             )
#
#     return app_portal(request, 'events', 'events/portal.html', Event, stats,
#                       config_url=generate_portal_url('events'),
#                      )
