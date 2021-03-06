# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2020  Hybird
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

from django.db.transaction import atomic
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.core.exceptions import ConflictError
from creme.creme_core.models import CremeEntity, FieldsConfig
from creme.creme_core.views import generic, decorators
from creme.creme_core.views.decorators import jsonify

from creme.persons import get_organisation_model

from ... import billing
from ..forms import payment_information as pi_forms
from ..models import PaymentInformation


# @login_required
# @permission_required('billing')
# def add(request, entity_id):
#     return generic.add_to_entity(request, entity_id, pi_forms.PaymentInformationCreateForm,
#                                  _('New payment information in the organisation «%s»'),
#                                  entity_class=get_organisation_model(),
#                                  submit_label=_('Save the payment information'),
#                                 )
class PaymentInformationCreation(generic.AddingInstanceToEntityPopup):
    model = PaymentInformation
    form_class = pi_forms.PaymentInformationCreateForm
    permissions = 'billing'
    entity_id_url_kwarg = 'orga_id'
    entity_classes = get_organisation_model()
    title = _('New payment information in the organisation «{entity}»')


# @login_required
# @permission_required('billing')
# def edit(request, payment_information_id):
#     return generic.edit_related_to_entity(request, payment_information_id,
#                                           PaymentInformation, pi_forms.PaymentInformationEditForm,
#                                           _('Payment information for «%s»'),
#                                          )
class PaymentInformationEdition(generic.RelatedToEntityEditionPopup):
    model = PaymentInformation
    form_class = pi_forms.PaymentInformationEditForm
    permissions = 'billing'
    pk_url_kwarg = 'pinfo_id'
    title = _('Payment information for «{entity}»')


class PaymentInformationRelatedCreation(generic.AddingInstanceToEntityPopup):
    model = PaymentInformation
    form_class = pi_forms.PaymentInformationCreateForm
    permissions = 'billing'
    entity_classes = [
        billing.get_invoice_model(),
        billing.get_quote_model(),
        billing.get_sales_order_model(),
        billing.get_credit_note_model(),
        billing.get_template_base_model(),
    ]
    title = _('New payment information in the organisation «{entity}»')

    def check_related_entity_permissions(self, entity, user):
        super().check_related_entity_permissions(entity=entity, user=user)
        user.has_perm_to_change_or_die(entity.get_source())

    def get_title_format_data(self):
        data = super().get_title_format_data()
        # data['entity'] = self.get_related_entity().allowed_str(self.request.user)
        data['entity'] = self.get_related_entity().get_source().allowed_str(self.request.user)

        return data

    def set_entity_in_form_kwargs(self, form_kwargs):
        entity = self.get_related_entity()

        if self.entity_form_kwarg:
            # form_kwargs[self.entity_form_kwarg] = entity
            form_kwargs[self.entity_form_kwarg] = entity.get_source().get_real_entity()

    def form_valid(self, form):
        self.object = pi = form.save()

        entity = self.get_related_entity()
        entity.payment_info = pi
        entity.save()

        return HttpResponse(self.get_success_url(), content_type='text/plain')


@jsonify
@login_required
@permission_required('billing')
@decorators.POST_only
@atomic
def set_default(request, payment_information_id, billing_id):
    pi = get_object_or_404(PaymentInformation, pk=payment_information_id)
    # billing_doc = get_object_or_404(CremeEntity, pk=billing_id).get_real_entity()
    entity = get_object_or_404(CremeEntity.objects.select_for_update(), pk=billing_id)
    user = request.user

    real_model = entity.entity_type.model_class()

    # if not isinstance(billing_doc, (billing.get_invoice_model(), billing.get_quote_model(),
    #                                 billing.get_sales_order_model(), billing.get_credit_note_model(),
    #                                 billing.get_template_base_model(),
    #                                )
    #                  ):
    if real_model not in {billing.get_invoice_model(),
                          billing.get_quote_model(),
                          billing.get_sales_order_model(),
                          billing.get_credit_note_model(),
                          billing.get_template_base_model(),
                         }:
        raise Http404('This entity is not a billing document')

    # if FieldsConfig.get_4_model(billing_doc.__class__).is_fieldname_hidden('payment_info'):
    if FieldsConfig.get_4_model(real_model).is_fieldname_hidden('payment_info'):
        raise ConflictError('The field "payment_info" is hidden.')

    billing_doc = entity.get_real_entity()

    organisation = pi.get_related_entity()
    user.has_perm_to_view_or_die(organisation)
    user.has_perm_to_link_or_die(organisation)

    user.has_perm_to_change_or_die(billing_doc)

    inv_orga_source = billing_doc.get_source()
    if not inv_orga_source or inv_orga_source.id != organisation.id:
        raise Http404('No organisation in this invoice.')

    billing_doc.payment_info = pi
    billing_doc.save()

    return {}
