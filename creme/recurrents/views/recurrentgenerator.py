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

import warnings

from django.db.transaction import atomic
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
# from django.utils.translation import ugettext_lazy as _

from formtools.wizard.views import SessionWizardView

from creme.creme_core.auth import build_creation_perm as cperm
from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.views import generic

from .. import get_rgenerator_model
from ..constants import DEFAULT_HFILTER_RGENERATOR
from ..forms import recurrentgenerator as generator_forms


RecurrentGenerator = get_rgenerator_model()


class RecurrentGeneratorWizard(SessionWizardView):
    # NB: in deed, the second form is just a place holder ;
    #     it will be dynamically replaced by a form from 'recurrent_registry' (see get_form().
    form_list = [generator_forms.RecurrentGeneratorCreateForm] * 2
    template_name = 'creme_core/generics/blockform/add_wizard.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('recurrents'))
    # @method_decorator(permission_required('recurrents.add_recurrentgenerator'))
    @method_decorator(permission_required(cperm(RecurrentGenerator)))
    def dispatch(self, *args, **kwargs):
        # return super(RecurrentGeneratorWizard, self).dispatch(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def done(self, form_list, **kwargs):
        # generator_form = form_list[0]
        # resource_form  = form_list[1]
        generator_form, resource_form = form_list

        with atomic():
            generator_form.instance.template = resource_form.save()
            generator_form.save()

        return redirect(resource_form.instance)

    def get_context_data(self, form, **kwargs):
        # context = super(RecurrentGeneratorWizard, self).get_context_data(form=form, **kwargs)
        context = super().get_context_data(form=form, **kwargs)
        context['title'] = RecurrentGenerator.creation_label
        # context['submit_label'] = _('Save the generator')
        context['submit_label'] = RecurrentGenerator.save_label

        return context

    def get_form(self, step=None, data=None, files=None):
        from ..registry import recurrent_registry

        form = None

        # Step can be None (see WizardView doc)
        if step is None:
            step = self.steps.current

        if step == '1':
            prev_data =  self.get_cleaned_data_for_step('0')

            ctype = prev_data['ct']
            form_class = recurrent_registry.get_form_of_template(ctype)

            kwargs = self.get_form_kwargs(step)
            kwargs.update(data=data,
                          files=files,
                          prefix=self.get_form_prefix(step, None),
                          initial=self.get_form_initial(step),  # Not really useful here...
                          ct=ctype,
                         )
            form = form_class(**kwargs)
        else:
            # form = super(RecurrentGeneratorWizard, self).get_form(step, data, files)
            form = super().get_form(step, data, files)

        return form

    def get_form_kwargs(self, step):
        return {'user': self.request.user}


def abstract_edit_rgenerator(request, generator_id, form=generator_forms.RecurrentGeneratorEditForm):
    warnings.warn('recurrents.views.recurrentgenerator.abstract_edit_rgenerator() is deprecated ; '
                  'use the class-based view RecurrentGeneratorEdition instead.',
                  DeprecationWarning
                 )
    return generic.edit_entity(request, generator_id, RecurrentGenerator, form)


def abstract_view_rgenerator(request, generator_id,
                             template='recurrents/view_generator.html',
                            ):
    warnings.warn('recurrents.views.recurrentgenerator.abstract_view_rgenerator() is deprecated ; '
                  'use the class-based view RecurrentGeneratorDetail instead.',
                  DeprecationWarning
                 )
    return generic.view_entity(request, generator_id, RecurrentGenerator, template=template)


@login_required
@permission_required('recurrents')
def edit(request, generator_id):
    warnings.warn('recurrents.views.recurrentgenerator.edit() is deprecated.', DeprecationWarning)
    return abstract_edit_rgenerator(request, generator_id)


@login_required
@permission_required('recurrents')
def detailview(request, generator_id):
    warnings.warn('recurrents.views.recurrentgenerator.detailview() is deprecated.', DeprecationWarning)
    return abstract_view_rgenerator(request, generator_id)


@login_required
@permission_required('recurrents')
def listview(request):
    return generic.list_view(request, RecurrentGenerator, hf_pk=DEFAULT_HFILTER_RGENERATOR)


class RecurrentGeneratorDetail(generic.EntityDetail):
    model = RecurrentGenerator
    template_name = 'recurrents/view_generator.html'
    pk_url_kwarg = 'generator_id'


class RecurrentGeneratorEdition(generic.EntityEdition):
    model = RecurrentGenerator
    form_class = generator_forms.RecurrentGeneratorEditForm
    pk_url_kwarg = 'generator_id'
