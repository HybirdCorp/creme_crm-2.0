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
from json import dumps as json_dumps
import logging
# import warnings

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Q, FieldDoesNotExist, ProtectedError
from django.db.transaction import atomic
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _, ugettext, ungettext

from .. import constants
from ..auth.decorators import login_required, superuser_required
from ..core.exceptions import ConflictError, SpecificProtectedError
from ..core.paginator import FlowPaginator
from ..forms import CremeEntityForm
from ..forms.bulk import BulkDefaultEditForm
from ..forms.merge import form_factory as merge_form_factory, MergeEntitiesBaseForm
# from ..gui.bulk_update import bulk_update_registry, FieldNotAllowed
from ..gui import bulk_update  # NB: do no import <bulk_update_registry> to facilitate unit testing
from ..models import CremeEntity, EntityCredentials, FieldsConfig, Relation, Sandbox
from ..models.fields import UnsafeHTMLField
from ..utils import (get_ct_or_404, get_from_POST_or_404, get_from_GET_or_404,
        bool_from_str_extended)
from ..utils.translation import get_model_verbose_name
from ..utils.html import sanitize_html
from ..utils.meta import ModelFieldEnumerator

from . import generic
from .decorators import jsonify, POST_only
from .generic import base, listview  # inner_popup
from .utils import build_cancel_path


logger = logging.getLogger(__name__)


@login_required
@jsonify
def get_creme_entities_repr(request, entities_ids):
    # With the url regexp we are sure that int() will work
    e_ids = [int(e_id) for e_id in entities_ids.split(',') if e_id]

    entities = CremeEntity.objects.in_bulk(e_ids)
    CremeEntity.populate_real_entities(list(entities.values()))

    user = request.user
    has_perm = user.has_perm_to_view

    return [{'id': e_id,
             'text': entity.get_real_entity().get_entity_summary(user)
                     if has_perm(entity) else
                     ugettext('Entity #{id} (not viewable)').format(id=e_id)
            } for e_id, entity in ((e_id, entities.get(e_id)) for e_id in e_ids)
                if entity is not None
           ]


@login_required
def get_sanitized_html_field(request, entity_id, field_name):
    """Used to show an HTML document in an <iframe>."""
    entity = get_object_or_404(CremeEntity, pk=entity_id)
    request.user.has_perm_to_view_or_die(entity)

    entity = entity.get_real_entity()

    try:
        field = entity._meta.get_field(field_name)
    except FieldDoesNotExist as e:
        raise ConflictError('This field does not exist.') from e

    if not isinstance(field, UnsafeHTMLField):
        raise ConflictError('This field is not an HTMLField.')

    unsafe_value = getattr(entity, field_name)

    return HttpResponse('' if not unsafe_value else
                        sanitize_html(unsafe_value,
                                      allow_external_img=request.GET.get('external_img', False),
                                     )
                       )


# TODO: bake the result in HTML instead of ajax view ??
@jsonify
@login_required
def get_info_fields(request, ct_id):
    ct = get_ct_or_404(ct_id)
    model = ct.model_class()

    if not issubclass(model, CremeEntity):
        raise Http404('No a CremeEntity subclass: {}'.format(model))

    # TODO: use django.forms.models.fields_for_model ?
    form = modelform_factory(model, CremeEntityForm)(user=request.user)
    required_fields = [name for name, field in form.fields.items()
                           if field.required and name != 'user'
                      ]

    kwargs = {}
    if len(required_fields) == 1:
        required_field = required_fields[0]
        kwargs['printer'] = lambda field: str(field.verbose_name) \
                                          if field.name != required_field else \
                                          ugettext('{field} [CREATION]').format(field=field.verbose_name)

    is_hidden = FieldsConfig.get_4_model(model).is_field_hidden

    return ModelFieldEnumerator(model).filter(viewable=True)\
                                      .exclude(lambda f, deep: is_hidden(f))\
                                      .choices(**kwargs)


@login_required
def clone(request):
    # TODO: Improve credentials ?
    entity_id = get_from_POST_or_404(request.POST, 'id')
    entity    = get_object_or_404(CremeEntity, pk=entity_id).get_real_entity()

    if entity.get_clone_absolute_url() != CremeEntity.get_clone_absolute_url():
        raise Http404(ugettext('This model does not use the generic clone view.'))

    user = request.user
    user.has_perm_to_create_or_die(entity)
    user.has_perm_to_view_or_die(entity)

    new_entity = entity.clone()

    if request.is_ajax():
        return HttpResponse(new_entity.get_absolute_url())

    return redirect(new_entity)


@login_required
def search_and_view(request):
    GET = request.GET
    model_ids = get_from_GET_or_404(GET, 'models').split(',')
    fields    = get_from_GET_or_404(GET, 'fields').split(',')
    value     = get_from_GET_or_404(GET, 'value')

    if not value:  # Avoid useless queries
        raise Http404('Void "value" arg')

    user = request.user
    check_app = user.has_perm_to_access_or_die
    models = []

    for model_id in model_ids:
        try:
            ct = ContentType.objects.get_by_natural_key(*model_id.split('-'))
        except (ContentType.DoesNotExist, TypeError) as e:
            raise Http404('This model does not exist: {}'.format(model_id)) from e

        check_app(ct.app_label)

        model = ct.model_class()

        if issubclass(model, CremeEntity):
            models.append(model)

    if not models:
        raise Http404('No valid model')

    fconfigs = FieldsConfig.get_4_models(models)

    for model in models:
        query = Q()

        for field_name in fields:
            try:
                field = model._meta.get_field(field_name)
            except FieldDoesNotExist:
                pass
            else:
                if fconfigs[model].is_field_hidden(field):
                    raise ConflictError(ugettext('This field is hidden.'))

                query |= Q(**{field.name: value})

        if query:  # Avoid useless query
            found = EntityCredentials.filter(user, model.objects.filter(query)).first()

            if found:
                return redirect(found)

    raise Http404(ugettext('No entity corresponding to your search was found.'))


# TODO: remove when bulk_update_registry has been rework to manage different type of cells (eg: RelationType => LINK)
def _bulk_has_perm(entity, user):  # NB: indeed 'entity' can be a simple model...
    owner = entity.get_related_entity() if hasattr(entity, 'get_related_entity') else entity  # TODO: factorise
    return user.has_perm_to_change(owner) if isinstance(owner, CremeEntity) else False


# @login_required
# def inner_edit_field(request, ct_id, id, field_name):
#     user = request.user
#     model = get_ct_or_404(ct_id).model_class()
#     instance = get_object_or_404(model, pk=id)
#
#     if not _bulk_has_perm(instance, user):
#         raise PermissionDenied(_('You are not allowed to edit this entity'))
#
#     try:
#         form_class = bulk_update.bulk_update_registry.get_form(model, field_name, BulkDefaultEditForm)
#
#         if request.method == 'POST':
#             form = form_class(entities=[instance], user=user, data=request.POST)  # todo: rename 'entities' arg
#
#             if form.is_valid():
#                 form.save()
#         else:
#             form = form_class(entities=[instance], user=user)
#     except (FieldDoesNotExist, bulk_update.FieldNotAllowed):
#         return HttpResponseBadRequest(_('The field «{}» does not exist or cannot be edited').format(field_name))
#
#     return inner_popup(request, 'creme_core/generics/blockform/edit_popup.html',
#                        {'form':  form,
#                         'title': _('Edit «{object}»').format(object=instance),
#                        },
#                        is_valid=form.is_valid(),
#                        reload=False, delegate_reload=True,
#                       )
class InnerEdition(base.ContentTypeRelatedMixin, generic.CremeModelEditionPopup):
    # model = ...
    # form_class = ...
    pk_url_kwarg = 'id'

    field_name_url_kwarg = 'field_name'
    bulk_update_registry = bulk_update.bulk_update_registry

    def check_instance_permissions(self, instance, user):
        super().check_instance_permissions(instance=instance, user=user)

        if not _bulk_has_perm(instance, user):
            raise PermissionDenied(ugettext('You are not allowed to edit this entity'))

    def dispatch(self, *args, **kwargs):
        try:
            return super().dispatch(*args, **kwargs)
        except (FieldDoesNotExist, bulk_update.FieldNotAllowed) as e:
            return HttpResponseBadRequest(str(e))

    def get_form_class(self):
        return self.bulk_update_registry \
                   .get_form(model=self.object.__class__,
                             field_name=self.kwargs[self.field_name_url_kwarg],
                             default=BulkDefaultEditForm,
                            )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        del kwargs['instance']  # TODO: use CremeEdition & remove this ?
        kwargs['entities'] = [self.object]  # TODO: rename 'entities' arg

        return kwargs

    def get_queryset(self):
        return self.get_ctype().model_class()._default_manager.all()


# @login_required
# def bulk_update_field(request, ct_id, field_name=None):
#     user = request.user
#     model = get_ct_or_404(ct_id).model_class()
#
#     if not issubclass(model, CremeEntity):  # todo: auxiliary too ? (see inner_edit_field())
#         raise Http404('The model must be a CremeEntity')
#
#     if field_name is None:
#         field_name = bulk_update.bulk_update_registry.get_default_field(model).name
#
#     try:
#         form_class = bulk_update.bulk_update_registry.get_form(model, field_name, BulkDefaultEditForm)
#     except (FieldDoesNotExist, bulk_update.FieldNotAllowed):
#         return HttpResponseBadRequest(ugettext('The field «{}» does not exist or cannot be edited').format(field_name))
#
#     meta = model._meta
#
#     if request.method == 'POST':
#         entity_ids = request.POST.getlist('entities', [])
#         entities = model.objects.filter(pk__in=entity_ids)
#         filtered = EntityCredentials.filter(user, entities, perm=EntityCredentials.CHANGE)
#
#         if not filtered:
#             raise PermissionDenied(ugettext('You are not allowed to edit these entities'))
#
#         form = form_class(entities=filtered, user=user, data=request.POST, is_bulk=True)
#
#         if form.is_valid():
#             form.save()
#             initial_count = len(entity_ids)
#             success_count = len(form.bulk_cleaned_entities)
#             invalid_count = len(form.bulk_invalid_entities)
#             forbidden_count = initial_count - success_count - invalid_count
#
#             context = {'model': get_model_verbose_name(model, success_count),
#                        'success': success_count,
#                        'initial': initial_count,
#                        'invalid': invalid_count,
#                        'forbidden': forbidden_count,
#                       }
#
#             # todo: modification_label/bulk_label/... in model instead (fr: masculin/féminin)
#             if initial_count == success_count:
#                 summary = ungettext('{success} «{model}» has been successfully modified.',
#                                     '{success} «{model}» have been successfully modified.',
#                                     success_count
#                                    )
#             else:
#                 summary = ungettext('{success} of {initial} «{model}» has been successfully modified.',
#                                     '{success} of {initial} «{model}» have been successfully modified.',
#                                     success_count
#                                    )
#
#                 if forbidden_count:
#                     summary += ' ' + ungettext('{forbidden} was not editable.',
#                                                '{forbidden} were not editable.',
#                                                forbidden_count
#                                               )
#
#                 if invalid_count:
#                     summary += ' ' + ungettext('{invalid} has returned an error.',
#                                                '{invalid} have returned an error.',
#                                                invalid_count
#                                               )
#
#             return render(request, 'creme_core/frags/bulk_process_report.html',
#                           {'form':  form,
#                            'title': _('Multiple update'),
#                            'summary': summary.format(**context),
#                           },
#                          )
#     else:
#         form = form_class(entities=(), user=user, is_bulk=True)
#
#     # todo: select_label in model instead (fr: masculin/féminin)
#     # help_message = u'<span class="bulk-selection-summary" data-msg="%s" data-msg-plural="%s"></span>' % (
#     #                      _(u'%%s «%s» has been selected.') % meta.verbose_name,
#     #                      _(u'%%s «%s» have been selected.') % meta.verbose_name_plural,
#     #                 )
#     help_message = format_html(
#         '<span class="bulk-selection-summary" data-msg="{msg}" data-msg-plural="{plural}"></span>',
#         msg=ugettext('%s «{model}» has been selected.').format(model=meta.verbose_name),
#         plural=ugettext('%s «{model}» have been selected.').format(model=meta.verbose_name_plural),
#     )
#
#     return inner_popup(request, 'creme_core/generics/blockform/edit_popup.html',
#                        {'form':  form,
#                         'title': _('Multiple update'),
#                         # 'help_message': mark_safe(help_message),
#                         'help_message': help_message,
#                        },
#                        is_valid=form.is_valid(),
#                        reload=False, delegate_reload=True,
#                       )
# TODO: factorise with InnerEdition
class BulkUpdate(base.EntityCTypeRelatedMixin, generic.CremeEditionPopup):
    # model = ...
    # form_class = ...
    # pk_url_kwarg = ...
    title = _('Multiple update')

    field_name_url_kwarg = 'field_name'
    bulk_update_registry = bulk_update.bulk_update_registry

    def dispatch(self, *args, **kwargs):
        try:
            return super().dispatch(*args, **kwargs)
        except (FieldDoesNotExist, bulk_update.FieldNotAllowed) as e:
            return HttpResponseBadRequest(str(e))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        meta = self.get_ctype().model_class()._meta
        # TODO: select_label in model instead (fr: masculin/féminin)
        context['help_message'] = format_html(
            '<span class="bulk-selection-summary" data-msg="{msg}" data-msg-plural="{plural}"></span>',
            msg=ugettext('{count} «{model}» has been selected.')
                        .format(count='%s', model=meta.verbose_name),
            plural=ugettext('{count} «{model}» have been selected.')
                           .format(count='%s', model=meta.verbose_name_plural),
        )

        return context

    def get_form_class(self):
        model = self.get_ctype().model_class()
        registry = self.bulk_update_registry
        field_name = self.kwargs.get(self.field_name_url_kwarg)

        if field_name is None:
            field_name = registry.get_default_field(model).name

        return registry.get_form(model=model,
                                 field_name=field_name,
                                 default=BulkDefaultEditForm,
                                )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entities'] = self.get_entities()
        kwargs['is_bulk'] = True

        return kwargs

    def get_summary(self, form):
        initial_count = len(self.get_entity_ids())
        success_count = len(form.bulk_cleaned_entities)
        invalid_count = len(form.bulk_invalid_entities)
        forbidden_count = initial_count - success_count - invalid_count

        context = {
            'model': get_model_verbose_name(form.model, success_count),
            'success': success_count,
            'initial': initial_count,
            'invalid': invalid_count,
            'forbidden': forbidden_count,
        }

        # TODO: modification_label/bulk_label/... in model instead (fr: masculin/féminin)
        if initial_count == success_count:
            summary = ungettext(
                '{success} «{model}» has been successfully modified.',
                '{success} «{model}» have been successfully modified.',
                success_count
            )
        else:
            summary = ungettext(
                '{success} of {initial} «{model}» has been successfully modified.',
                '{success} of {initial} «{model}» have been successfully modified.',
                success_count
            )

            if forbidden_count:
                summary += ' ' + ungettext('{forbidden} was not editable.',
                                           '{forbidden} were not editable.',
                                           forbidden_count
                                          )

            if invalid_count:
                summary += ' ' + ungettext('{invalid} has returned an error.',
                                           '{invalid} have returned an error.',
                                           invalid_count
                                          )

        return summary.format(**context)

    # TODO: avoid the use of 2 templates ?
    def form_valid(self, form):
        super().form_valid(form=form)

        return render(
            self.request,
            template_name='creme_core/frags/bulk_process_report.html',  # TODO: attributes ?
            context={
                'form': form,
                'title': self.get_title(),
                'summary': self.get_summary(form=form),
            },
        )

    def get_entity_ids(self):
        return self.request.POST.getlist('entities', [])

    def get_entities(self):
        if self.request.method == 'POST':
            entity_ids = self.get_entity_ids()
            # NB (#60): 'SELECT FOR UPDATE' in a query using an 'OUTER JOIN' and nullable ids will fail with postgresql (both 9.6 & 10.x).
            # TODO: This bug may be fixed in django>=2.0 (see https://code.djangoproject.com/ticket/28010)
            # entities = self.get_queryset().select_for_update().filter(pk__in=entity_ids)
            qs = self.get_queryset()
            entities = qs.filter(pk__in=entity_ids)

            filtered = EntityCredentials.filter(self.request.user,
                                                queryset=entities,
                                                perm=EntityCredentials.CHANGE,
                                               )

            if not filtered:
                raise PermissionDenied(_('You are not allowed to edit these entities'))

            # NB (#60): Move 'SELECT FOR UPDATE' here for now. It could cause performance issues
            # with a large amount of selected entities, but this never happens with common use cases.
            # return filtered
            return qs.select_for_update().filter(pk__in=filtered)
        else:
            return ()

    def get_queryset(self):
        return self.get_ctype().model_class()._default_manager.all()


@login_required
def select_entity_for_merge(request):
    entity1_id = get_from_GET_or_404(request.GET, 'id1', cast=int)
    entity1 = get_object_or_404(CremeEntity, pk=entity1_id)

    if merge_form_factory(entity1.entity_type.model_class()) is None:
        raise ConflictError('This type of entity cannot be merged')

    user = request.user
    user.has_perm_to_view_or_die(entity1); user.has_perm_to_change_or_die(entity1)

    return listview.list_view_popup(request,
                                    model=entity1.entity_type.model_class(),  # NB: avoid retrieving real entity...
                                    mode=listview.MODE_SINGLE_SELECTION,
                                    extra_q=~Q(pk=entity1_id),
                                   )


@login_required
@atomic
def merge(request):
    GET = request.GET
    entity1_id = get_from_GET_or_404(GET, 'id1', cast=int)
    entity2_id = get_from_GET_or_404(GET, 'id2', cast=int)

    if entity1_id == entity2_id:
        raise ConflictError('You can not merge an entity with itself.')

    entities = CremeEntity.objects.all()

    if request.method == 'POST':
        entities = entities.select_for_update()

    entities_per_id = entities.in_bulk((entity1_id, entity2_id))

    try:
        entity1 = entities_per_id[entity1_id]
        entity2 = entities_per_id[entity2_id]
    except IndexError as e:
        raise Http404('Entity not found: {}'.format(e)) from e

    if entity1.entity_type_id != entity2.entity_type_id:
        raise ConflictError('You can not merge entities of different types.')

    user = request.user
    can_view = user.has_perm_to_view_or_die
    can_view(entity1); user.has_perm_to_change_or_die(entity1)
    can_view(entity2); user.has_perm_to_delete_or_die(entity2)

    # TODO: try to swap 1 & 2

    real_entity1 = entity1.get_real_entity()
    real_entity2 = entity2.get_real_entity()

    # TODO: 'merge_form_registry' as attribute in the future CBV + pass it as argument here
    EntitiesMergeForm = merge_form_factory(real_entity1.__class__)

    if EntitiesMergeForm is None:
        raise ConflictError('This type of entity cannot be merged')

    if request.method == 'POST':
        POST = request.POST
        merge_form = EntitiesMergeForm(user=request.user, data=POST,
                                       entity1=real_entity1,
                                       entity2=real_entity2,
                                      )

        if merge_form.is_valid():
            merge_form.save()

            # NB: we get the entity1 attribute (ie: not the local variable),
            # because the entities can be swapped in the form (but form.entity1
            # is always kept & form.entity2 deleted).
            return redirect(merge_form.entity1)

        cancel_url = POST.get('cancel_url')
    else:
        try:
            merge_form = EntitiesMergeForm(user=request.user,
                                           entity1=real_entity1,
                                           entity2=real_entity2,
                                          )
        except MergeEntitiesBaseForm.CanNotMergeError as e:
            raise ConflictError(e) from e

        cancel_url = build_cancel_path(request)

    return render(request,
                  'creme_core/forms/merge.html',
                  {'form':   merge_form,
                   'title': ugettext('Merge «{entity1}» with «{entity2}»').format(
                                   entity1=real_entity1,
                                   entity2=real_entity2,
                                ),
                   'help_message': _('You are going to merge two entities into a new one.\n'
                                     'Choose which information you want the old entities '
                                     'give to the new entity.\n'
                                     'The relationships, the properties and the other links '
                                     'with any of old entities will be automatically '
                                     'available in the new merged entity.'
                                    ),
                   'submit_label': _('Merge'),
                   'cancel_url': cancel_url,
                  }
                 )


# @login_required
# def trash(request):
#     return render(request, 'creme_core/trash.html',
#                   context={'bricks_reload_url': reverse('creme_core__reload_bricks')},
#                  )
class Trash(generic.BricksView):
    template_name = 'creme_core/trash.html'


@login_required
@POST_only
def empty_trash(request):
    user = request.user

    # We try to delete the remaining entities (which could not be deleted 
    # because of relationships) when there are errors, while the previous 
    # iteration managed to remove some entities.
    # It will not work with cyclic references (but it is certainly very unusual).
    while True:
        progress = False
        errors = []  # TODO: LimitedList
        # NB: we do not use delete() method of queryset in order to send signals
        entities = EntityCredentials.filter_entities(
                        user,
                        CremeEntity.objects.filter(is_deleted=True),
                        EntityCredentials.DELETE,
                    )
        paginator = FlowPaginator(queryset=entities.order_by('id'),
                                  key='id', per_page=1024,
                                 )

        # TODO: select_for_update() ?
        for entities_page in paginator.pages():
            entities = entities_page.object_list

            CremeEntity.populate_real_entities(entities)

            for entity in entities:
                entity = entity.get_real_entity()

                try:
                    entity.delete()
                except ProtectedError:
                    errors.append(ugettext('«{entity}» can not be deleted because of its dependencies.').format(
                                        entity=entity.allowed_str(user)
                                    )
                                 )
                except Exception as e:
                    logger.exception('Error when trying to empty the trash')
                    errors.append(ugettext('«{entity}» deletion caused an unexpected error [{error}].').format(
                                        entity=entity.allowed_str(user),
                                        error=e,
                                    )
                                 )
                else:
                    progress = True

        if not errors or not progress:
            break

    # TODO: factorise ??
    if not errors:
        status = 200
        message = ugettext('Operation successfully completed')
    else:
        status = 409
        message = format_html(
            '{}<ul>{}</ul>',
            ugettext('The following entities cannot be deleted'),
            format_html_join('', '<li>{}</li>', ((msg,) for msg in errors)),
        )

    return HttpResponse(message, status=status)


@login_required
@POST_only
@atomic
def restore_entity(request, entity_id):
    # entity = get_object_or_404(CremeEntity.objects.filter(is_deleted=True), pk=entity_id) \
    #                                               .get_real_entity()
    entity = get_object_or_404(CremeEntity.objects.select_for_update(),
                               pk=entity_id, is_deleted=True,
                              ).get_real_entity()

    if entity.get_delete_absolute_url() != CremeEntity.get_delete_absolute_url(entity):
        raise Http404(ugettext('This model does not use the generic deletion view.'))

    if hasattr(entity, 'get_related_entity'):
        raise Http404('Can not restore an auxiliary entity')  # See trash_entity()

    request.user.has_perm_to_delete_or_die(entity)
    entity.restore()

    if request.is_ajax():
        return HttpResponse()

    return redirect(entity)


def _delete_entity(user, entity):
    if entity.get_delete_absolute_url() != CremeEntity.get_delete_absolute_url(entity):
        return (404,
                ugettext('«{entity}» does not use the generic deletion view.').format(
                        entity=entity.allowed_str(user),
                    )
               )

    if hasattr(entity, 'get_related_entity'):
        related = entity.get_related_entity()

        if related is None:
            logger.critical('delete_entity(): an auxiliary entity seems orphan (id=%s)', entity.id)
            return 403, ugettext('You are not allowed to delete this entity: {}').format(entity.allowed_str(user))

        if not user.has_perm_to_change(related):
            return 403, ugettext('{entity} : <b>Permission denied</b>').format(entity=entity.allowed_str(user))

        trash = False
    else:
        if not user.has_perm_to_delete(entity):
            return 403, ugettext('{entity} : <b>Permission denied</b>').format(entity=entity.allowed_str(user))

        trash = not entity.is_deleted

    try:
        if trash:
            entity.trash()
        else:
            entity.delete()
    except SpecificProtectedError as e:
        return (400,
                '{} {}'.format(
                    ugettext('«{entity}» can not be deleted.').format(entity=entity.allowed_str(user)),
                    e.args[0],
                  ),
               )
    except ProtectedError as e:
        return (400,
                ugettext('«{entity}» can not be deleted because of its dependencies.').format(
                        entity=entity.allowed_str(user),
                    ),
                {'protected_objects': e.args[1]},
               )
    except Exception as e:
        logger.exception('Error when trying to empty the trash')
        return (400,
                ugettext('«{entity}» deletion caused an unexpected error [{error}].').format(
                        entity=entity.allowed_str(user),
                        error=e,
                    )
               )


@login_required
@atomic
def delete_entities(request):
    "Delete several CremeEntities, with a Ajax call (POST method)."
    try:
        entity_ids = [int(e_id) for e_id in get_from_POST_or_404(request.POST, 'ids').split(',') if e_id]
    except ValueError:
        return HttpResponse('Bad POST argument', status=400)

    if not entity_ids:
        return HttpResponse(ugettext('No selected entities'), status=400)

    logger.debug('delete_entities() -> ids: %s ', entity_ids)

    user     = request.user
    # entities = list(CremeEntity.objects.filter(pk__in=entity_ids))
    entities = list(CremeEntity.objects.select_for_update().filter(pk__in=entity_ids))
    errors   = defaultdict(list)

    len_diff = len(entity_ids) - len(entities)
    if len_diff:
        errors[404].append(ungettext("{count} entity doesn't exist or has been removed.",
                                     "{count} entities don't exist or have been removed.",
                                     len_diff
                                    ).format(count=len_diff)
                          )

    CremeEntity.populate_real_entities(entities)

    for entity in entities:
        error = _delete_entity(user, entity.get_real_entity())
        if error:
            errors[error[0]].append(error[1])  # TODO: use error[2] if exists ??

    if not errors:
        status = 200
        message = ugettext('Operation successfully completed')
        content_type = None
    else:
        status = min(errors)
        message = json_dumps({'count': len(entity_ids),
                              'errors': [msg for error_messages in errors.values() for msg in error_messages],
                             }
                            )
        content_type = 'application/json'

    return HttpResponse(message, content_type=content_type, status=status)


@login_required
@POST_only
@atomic
def delete_entity(request, entity_id):
    # entity = get_object_or_404(CremeEntity, pk=entity_id).get_real_entity()
    entity = get_object_or_404(CremeEntity.objects.select_for_update(),
                               pk=entity_id,
                              ).get_real_entity()
    error = _delete_entity(request.user, entity)

    if error:
        # code, msg, args = error if len(error) == 3 else error + ({},)
        code, msg, *args = error

        if code == 404: raise Http404(msg)
        # TODO: 400 => ConflictError ??

        def _deps_as_str(d):
            if not isinstance(d, dict):
                return '??'

            user = request.user
            deps = []
            for dep in d.get('protected_objects', ())[:10]:
                if isinstance(dep, Relation):
                    deps.append('{} «{}»'.format(
                        dep.type.predicate,
                        dep.object_entity.allowed_str(user),
                    ))
                elif isinstance(dep, CremeEntity):
                    deps.append(dep.allowed_str(user))
                else:
                    deps.append(str(dep))

            return ', '.join(deps)

        # raise PermissionDenied(msg, args)
        raise PermissionDenied(
            msg if not args else '{} ({})'.format(msg, _deps_as_str(args[0]))
        )

    url = (entity.get_lv_absolute_url()                   if hasattr(entity, 'get_lv_absolute_url') else
           entity.get_related_entity().get_absolute_url() if hasattr(entity, 'get_related_entity') else
           reverse('creme_core__home'))

    if request.is_ajax():
        # NB: we redirect because this view can be used from the detail-view
        #     (if it's a definitive deletion, we MUST go to a new page anyway)
        return HttpResponse(url, content_type='text/plain')

    return HttpResponseRedirect(url)


@login_required
def delete_related_to_entity(request, ct_id):
    """Delete a model related to a CremeEntity.
    @param request: Request with POST method ; POST data should contain an 'id'(=pk) value.
    @param ct_id: ContentType ID of a django model class which implements the method get_related_entity().
    """
    model = get_ct_or_404(ct_id).model_class()
    if issubclass(model, CremeEntity):
        raise Http404('This view can not delete CremeEntities.')

    auxiliary = get_object_or_404(model, pk=get_from_POST_or_404(request.POST, 'id'))
    entity = auxiliary.get_related_entity()

    request.user.has_perm_to_change_or_die(entity)

    try:
        auxiliary.delete()
    except ProtectedError as e:
        raise PermissionDenied(e.args[0]) from e

    if request.is_ajax():
        return HttpResponse()

    return redirect(entity)


@login_required
@superuser_required
@POST_only
@atomic
def restrict_to_superusers(request):
    POST = request.POST
    set_sandbox = get_from_POST_or_404(POST, 'set', cast=bool_from_str_extended, default='1')
    # entity = get_object_or_404(CremeEntity, id=get_from_POST_or_404(POST, 'id', cast=int))
    entity = get_object_or_404(
        CremeEntity.objects.select_for_update(),
        id=get_from_POST_or_404(POST, 'id', cast=int),
    )

    if set_sandbox:
        if entity.sandbox_id:
            raise ConflictError('This entity is already in a sandbox.')

        entity.sandbox = Sandbox.objects.get(uuid=constants.UUID_SANDBOX_SUPERUSERS)
        entity.save()
    else:
        sandbox = entity.sandbox

        if not sandbox or str(sandbox.uuid) != constants.UUID_SANDBOX_SUPERUSERS:
            raise ConflictError('This entity is not in the "Restricted to superusers" sandbox.')

        entity.sandbox = None
        entity.save()

    return HttpResponse()


@login_required
def list_view_popup(request):
    """ Displays a list-view selector in an inner popup.

    GET arguments are:
      - 'ct_id': the ContentType ID of the model we want. Required (if not given in the URL -- which is deprecated).
      - 'selection': The selection mode, which can be "single" or "multiple". Optional (default is "single").
    """
    if request.method == 'POST':
        POST = request.POST
        ct_id = get_from_POST_or_404(POST, 'ct_id', cast=int)
        mode  = get_from_POST_or_404(POST, 'selection', cast=listview.str_to_mode, default='single')
    else:
        GET = request.GET
        ct_id = get_from_GET_or_404(GET, 'ct_id', cast=int)
        mode  = get_from_GET_or_404(GET, 'selection', cast=listview.str_to_mode, default='single')

    ct = get_ct_or_404(ct_id)
    lv_state_id = '{}#{}'.format(ct_id, request.path)

    return listview.list_view_popup(request, model=ct.model_class(), mode=mode, lv_state_id=lv_state_id)
