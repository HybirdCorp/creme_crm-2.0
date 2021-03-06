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

import logging
import warnings

from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth import build_creation_perm as cperm
from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.views import generic

from .. import get_folder_model
from ..constants import DEFAULT_HFILTER_FOLDER
from ..forms import folder as f_forms


logger = logging.getLogger(__name__)
Folder = get_folder_model()


# Function views --------------------------------------------------------------

def abstract_add_folder(request, form=f_forms.FolderForm,
                        submit_label=Folder.save_label,
                       ):
    warnings.warn('documents.views.folder.abstract_add_folder() is deprecated ; '
                  'use the class-based view FolderDetail instead.',
                  DeprecationWarning
                 )
    return generic.add_entity(request, form,
                              extra_template_dict={'submit_label': submit_label},
                             )


# def abstract_add_child_folder(request, folder_id, form=f_forms.ChildFolderForm,
#                               title=_('New child folder for «%s»'),
#                               submit_label=Folder.save_label,
#                             ):
#     parent_folder = get_object_or_404(Folder, id=folder_id)
#     user = request.user
#
#     user.has_perm_to_link_or_die(parent_folder)
#
#     return generic.add_model_with_popup(
#         request, form,
#         title=title % parent_folder.allowed_str(user),
#         initial={'parent': parent_folder},
#         submit_label=submit_label,
#     )


def abstract_edit_folder(request, folder_id, form=f_forms.FolderForm):
    warnings.warn('documents.views.folder.abstract_edit_folder() is deprecated ; '
                  'use the class-based view FolderEdition instead.',
                  DeprecationWarning
                 )
    return generic.edit_entity(request, folder_id, Folder, form)


def abstract_view_folder(request, folder_id,
                         template='documents/view_folder.html',
                        ):
    warnings.warn('documents.views.folder.abstract_view_folder() is deprecated ; '
                  'use the class-based view FolderDetail instead.',
                  DeprecationWarning
                 )
    return generic.view_entity(request, folder_id, Folder, template=template)


def abstract_list_folders(request, **extra_kwargs):
    parent_id   = request.POST.get('parent_id') or request.GET.get('parent_id')
    extra_q     = Q(parent_folder__isnull=True)
    previous_id = None
    folder      = None

    if parent_id is not None:
        try:
            parent_id = int(parent_id)
        except (ValueError, TypeError):
            logger.warning('Folder.listview(): invalid "parent_id" parameter: %s', parent_id)
            parent_id = None
        else:
            folder = get_object_or_404(Folder, pk=parent_id)
            request.user.has_perm_to_view_or_die(folder)
            extra_q = Q(parent_folder=folder)
            previous_id = folder.parent_folder_id

    def post_process(template_dict, request):
        if folder is not None:
            parents = folder.get_parents()
            template_dict['list_title'] = _('List sub-folders of «{}»').format(folder)

            if parents:
                parents.reverse()
                parents.append(folder)
                template_dict['list_sub_title'] = ' > '.join(f.title for f in parents)

    return generic.list_view(
        request, Folder,
        hf_pk=DEFAULT_HFILTER_FOLDER,
        content_template='documents/frags/folder_listview_content.html',
        extra_q=extra_q,
        extra_dict={'parent_id': parent_id or '',
                    'extra_bt_templates': ('documents/frags/previous.html', ),
                    'previous_id': previous_id,
                   },
        post_process=post_process,
        **extra_kwargs
    )


@login_required
@permission_required(('documents', cperm(Folder)))
def add(request):
    warnings.warn('documents.views.folder.add() is deprecated.', DeprecationWarning)
    return abstract_add_folder(request)


# @login_required
# @permission_required(('documents', cperm(Folder)))
# def add_child(request, folder_id):
#     return abstract_add_child_folder(request, folder_id)


@login_required
@permission_required('documents')
def edit(request, folder_id):
    warnings.warn('documents.views.folder.edit() is deprecated.', DeprecationWarning)
    return abstract_edit_folder(request, folder_id)


@login_required
@permission_required('documents')
def detailview(request, folder_id):
    warnings.warn('documents.views.folder.abstract_view_folder() is deprecated.', DeprecationWarning)
    return abstract_view_folder(request, folder_id)


@login_required
@permission_required('documents')
def listview(request):
    return abstract_list_folders(request)


# Class-based views  ----------------------------------------------------------

class FolderCreation(generic.EntityCreation):
    model = Folder
    form_class = f_forms.FolderForm


# TODO: no CHANGE credentials for parent ?
# TODO: link-popup.html ?
class ChildFolderCreation(generic.AddingInstanceToEntityPopup):
    model = Folder
    form_class = f_forms.ChildFolderForm
    permissions = ['documents', cperm(Folder)]
    title = _('New child folder for «{entity}»')
    entity_id_url_kwarg = 'folder_id'
    entity_classes = Folder

    def check_view_permissions(self, user):
        super().check_view_permissions(user=user)
        user.has_perm_to_link_or_die(Folder, owner=None)


class FolderDetail(generic.EntityDetail):
    model = Folder
    template_name = 'documents/view_folder.html'
    pk_url_kwarg = 'folder_id'


class FolderEdition(generic.EntityEdition):
    model = Folder
    form_class = f_forms.FolderForm
    pk_url_kwarg = 'folder_id'
