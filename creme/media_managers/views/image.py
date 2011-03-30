# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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
from django.http import HttpResponse

from django.template import RequestContext, Template
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType

from creme_core.views.generic import add_entity, edit_entity, list_view, view_entity, list_view_popup_from_widget
#from creme_core.templatetags.creme_core_tags import image_size #TODO: move to media_managers ???

from media_managers.models import Image
from media_managers.forms.image import ImageForm
from creme.creme_core.utils import jsonify


@login_required
@permission_required('media_managers')
@permission_required('media_managers.add_image')
def add(request):
    req_get = request.GET.get
    kwargs = {}
    popup = req_get('popup')

    if popup is not None:
        popup = 'popup/'
        kwargs.update(template='creme_core/generics/blockform/add_popup.html')
    else:
        popup = ''

    return_path = '/media_managers/image/%s%%s?from_id=%s' % (popup, req_get('from_id', ''))

    return add_entity(request, ImageForm, return_path, **kwargs)

@login_required
@permission_required('media_managers')
def edit(request, image_id):
    return edit_entity(request, image_id, Image, ImageForm)

@login_required
@permission_required('media_managers')
def detailview(request, image_id):
    #'size':     image_size(image, max_h=2000, max_w=500)
    return view_entity(request, image_id, Image, '/media_managers/image', 'media_managers/view_image.html')

@login_required
@permission_required('media_managers')
def popupview(request, image_id):
    #TODO : Use inner popup ?
    return view_entity(request, image_id, Image, '/media_managers/image',
                       template='media_managers/view_image_popup.html',
                       extra_template_dict={'from_id': request.GET.get('from_id')}
                      )

@login_required
@permission_required('media_managers')
def listview(request):
    return list_view(request, Image, extra_dict={'add_url': '/media_managers/image/add'})

@login_required
@permission_required('media_managers')
def listview_popup(request):
    return list_view_popup_from_widget(request, ContentType.objects.get_for_model(Image).id, True)

@login_required
@permission_required('media_managers')
def select_image_tiny_mce(request):
    content = ""

    try:
        f = open("%s/tiny_mce/plugins/advimage/image.htm" % settings.MEDIA_ROOT, "r")
        content = f.read()
        f.close()
    except:
        pass

    return HttpResponse(Template(content).render(RequestContext(request, {})))

@jsonify
@login_required
@permission_required('media_managers')
def get_url(request, image_id):
    image = get_object_or_404(Image, pk=image_id)
    image.can_view_or_die(request.user)
    return {'url': image.get_image_url()}