# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2011  Hybird
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

from django.utils.translation import ugettext as _
from django.conf import settings

from creme_core.gui.field_printers import simple_print

from mediagenerator.utils import media_url


def print_phone(entity, fval, user):
    if not fval:
        return simple_print(entity, fval)

    return """%(number)s&nbsp;<a onclick="creme.cti.phoneCall('%(url)s', '%(number)s', %(id)s);">%(label)s<img src="%(img)s" alt="%(label)s"/></a>""" % {
            'url':    settings.ABCTI_URL,
            'number': fval,
            'id':     entity.id,
            'label':  _(u'Call'),
            'img':    media_url('images/phone_22.png'),
        }
