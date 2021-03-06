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
# from django.contrib.contenttypes.models import ContentType
# from django.template import Library
#
# from ..gui.quick_forms import quickforms_registry
# from ..utils.unicode_collation import collator
#
#
# register = Library()
#
#
# @register.inclusion_tag('creme_core/templatetags/quickforms_panel.html', takes_context=True)
# def get_quickforms_panel(context, target_node_id='sub_content'):
#     warnings.warn('The templatetags library "creme_quickforms" is deprecated.')
#
#     get_ct   = ContentType.objects.get_for_model
#     has_perm = context['request'].user.has_perm_to_create
#     content_types = [{'id':           get_ct(model).id,
#                       'verbose_name': model._meta.verbose_name
#                      } for model in quickforms_registry.iter_models() if has_perm(model)
#                     ]
#
#     sort_key = collator.sort_key
#     content_types.sort(key=lambda k: sort_key(k['verbose_name']))
#
#     context['content_types'] = content_types
#
#     return context
