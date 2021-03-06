# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2019  Hybird
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
# import warnings

from django.db.models.fields import FieldDoesNotExist
from django.db.transaction import atomic
from django.forms import Field, Widget, Select, CheckboxInput
from django.forms.models import fields_for_model, model_to_dict
from django.utils.translation import ugettext as _

from ..gui.merge import merge_form_registry
from ..models import CremeEntity, CustomField, CustomFieldValue, FieldsConfig
from ..signals import pre_merge_related
from ..utils import replace_related_object
from .base import CremeForm, _CUSTOM_NAME

logger = logging.getLogger(__name__)


class EntitiesHeaderWidget(Widget):
    template_name = 'creme_core/forms/widgets/merge/headers.html'

    def get_context(self, name, value, attrs):
        # TODO: remove 'ui-layout hbox' + improve class 'merge_entity_field' (+ rename 'merge-entity-field')
        extra_attrs = {'class': 'merge_entity_field ui-layout hbox'}
        if attrs is not None:
            extra_attrs.update(attrs)

        # context = super(EntitiesHeaderWidget, self).get_context(name=name, value=value, attrs=extra_attrs)
        context = super().get_context(name=name, value=value, attrs=extra_attrs)
        context['widget']['labels'] = value or ('', '', '')

        return context


class MergeWidget(Widget):
    template_name = 'creme_core/forms/widgets/merge/triple.html'

    def __init__(self, original_widget, *args, **kwargs):
        # super(MergeWidget, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self._original_widget = original_widget

    def get_context(self, name, value, attrs):
        # TODO: see EntitiesHeaderWidget
        extra_attrs = {'class': 'merge_entity_field ui-layout hbox'}
        if attrs is not None:
            extra_attrs.update(attrs)

        # context = super(MergeWidget, self).get_context(name=name, value=value, attrs=extra_attrs)
        context = super().get_context(name=name, value=value, attrs=extra_attrs)
        widget_cxt = context['widget']
        id_attr = widget_cxt['attrs']['id']

        value_1, value_2, value_m = value or ('', '', '')
        widget = self._original_widget
        # TODO: improve Wigdets with a 'read_only' param -> each type choose the right html attribute
        ro_attr = 'disabled' if isinstance(widget, (Select, CheckboxInput)) else 'readonly'

        # NB: the classes 'merge_entity1'/'merge_entity2'/'merge_result' won't be used by complexes Widget
        #     (eg: CalendarWidget) so the CSS 'width: 99%;' won't be used for them
        # TODO: is it a good way to do this ? (ex: always wrap widget in <div> for layout, & this layouts use
        #       the extra classes given in attrs).
        get_sub_context = self._original_widget.get_context
        widget_cxt['first']  = get_sub_context(name='{}_1'.format(name),
                                               value=value_1,
                                               attrs={'id': '{}_1'.format(id_attr),
                                                      ro_attr: '',
                                                      'class': 'merge_entity1',
                                                     },
                                              )['widget']
        widget_cxt['merged'] = get_sub_context(name='{}_merged'.format(name),
                                               value=value_m,
                                               attrs={'id': '{}_merged'.format(id_attr),
                                                      'class': 'merge_result',
                                                     },
                                             )['widget']
        widget_cxt['second'] = get_sub_context(name='{}_2'.format(name),
                                               value=value_2,
                                               attrs={'id': '{}_2'.format(id_attr),
                                                      ro_attr: '',
                                                      'class': 'merge_entity2',
                                                     },
                                             )['widget']

        return context

    def value_from_datadict(self, data, files, name):
        value_from_datadict = self._original_widget.value_from_datadict
        return (
            value_from_datadict(data=data, files=files, name='{}_1'.format(name)),
            value_from_datadict(data=data, files=files, name='{}_2'.format(name)),
            value_from_datadict(data=data, files=files, name='{}_merged'.format(name)),
        )


class MergeField(Field):
    def __init__(self, modelform_field, model_field, user=None, *args, **kwargs):
        # super(MergeField, self).__init__(self, widget=MergeWidget(modelform_field.widget), *args, **kwargs)
        super().__init__(widget=MergeWidget(modelform_field.widget), *args, **kwargs)

        self.required = modelform_field.required
        self._original_field = modelform_field
        self._restricted_queryset = None

        self.user = user

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, user):
        self._user = user
        self._original_field.user = user

    def clean(self, value):
        return self._original_field.clean(value[2])


class MergeEntitiesBaseForm(CremeForm):
    entities_labels = Field(label='', required=False, widget=EntitiesHeaderWidget)

    class CanNotMergeError(Exception):
        pass

    def __init__(self, entity1, entity2, *args, **kwargs):
        # super(MergeEntitiesBaseForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.entity1 = entity1
        self.entity2 = entity2

        user = self.user
        fields = self.fields

        build_initial = self._build_initial_dict
        entity1_initial = build_initial(entity1)
        entity2_initial = build_initial(entity2)

        # The older entity is preferred
        initial_index = 0 if entity1.modified <= entity2.modified else 1

        for name, field in fields.items():
            if name == 'entities_labels':
                field.initial = (str(entity1), str(entity2), _(u'Merged entity'))
            else:
                initial = [entity1_initial[name], entity2_initial[name]]
                # We try to initialize with preferred one, but we use the other if it is empty.
                initial.append(initial[initial_index] or initial[1 - initial_index])
                field.initial = initial

        # Custom fields --------------------------------------------------------
        # TODO: factorise (CremeEntityForm ? get_custom_fields_n_values ? ...)
        cfields = CustomField.objects.filter(content_type=entity1.entity_type)
        CremeEntity.populate_custom_values([entity1, entity2], cfields)
        self._customs = customs = [(cfield,
                                    entity1.get_custom_value(cfield),
                                    entity2.get_custom_value(cfield),
                                   ) for cfield in cfields
                                  ]

        for i, (cfield, cvalue1, cvalue2) in enumerate(customs):
            formfield1 = cfield.get_formfield(cvalue1)
            # fields[_CUSTOM_NAME % i] = merge_field = MergeField(formfield1,
            fields[_CUSTOM_NAME.format(i)] = merge_field = MergeField(formfield1,
                                                                model_field=None,
                                                                label=cfield.name,
                                                                user=user,
                                                               )

            initial = [formfield1.initial,
                       cfield.get_formfield(cvalue2).initial,
                      ]
            initial.append(initial[initial_index] or initial[1 - initial_index])
            merge_field.initial = initial

    def _build_initial_dict(self, entity):
        return model_to_dict(entity)

    def _post_entity1_update(self, entity1, entity2, cleaned_data):
        for i, (custom_field, cvalue1, cvalue2) in enumerate(self._customs):
            # value = cleaned_data[_CUSTOM_NAME % i]
            value = cleaned_data[_CUSTOM_NAME.format(i)]  # TODO: factorize with __init__() ?
            CustomFieldValue.save_values_for_entities(custom_field, [entity1], value)

            if cvalue2 is not None:
                cvalue2.delete()

    def clean(self):
        # cdata = super(MergeEntitiesBaseForm, self).clean()
        cdata = super().clean()

        if not self._errors:
            entity1 = self.entity1

            for name in self.fields:
                try:
                    mfield = entity1._meta.get_field(name)
                except FieldDoesNotExist:
                    pass
                else:
                    if not getattr(mfield, 'many_to_many', False):
                        setattr(entity1, name, cdata[name])

            entity1.full_clean()

        return cdata

    @atomic
    def save(self, *args, **kwargs):
        # super(MergeEntitiesBaseForm, self).save(*args, **kwargs)
        super().save(*args, **kwargs)
        cdata = self.cleaned_data

        entity1 = self.entity1
        entity2 = self.entity2

        entity1.save()
        self._post_entity1_update(entity1, entity2, cdata)
        pre_merge_related.send_robust(sender=entity1, other_entity=entity2)

        replace_related_object(entity2, entity1)

        # ManyToManyFields
        for m2m_field in entity1._meta.many_to_many:
            name = m2m_field.name
            m2m_data = cdata.get(name)
            if m2m_data is not None:
                getattr(entity1, name).set(m2m_data)

        try:
            entity2.delete()
        except Exception as e:
            logger.error('Error when merging 2 entities : the old one "%s"(id=%s) cannot be deleted: %s',
                         entity2, entity2.id, e
                        )


def mergefield_factory(modelfield):
    formfield = modelfield.formfield()

    if not formfield:  # Happens for cremeentity_ptr (OneToOneField)
        return None

    return MergeField(formfield, modelfield, label=modelfield.verbose_name)


def form_factory(model):
    # TODO: use a cache ??
    mergeform_factory = merge_form_registry.get(model)

    if mergeform_factory is not None:
        base_form_class = mergeform_factory()

        return type('Merge{}Form'.format(model.__name__), (base_form_class,),
                    fields_for_model(model, formfield_callback=mergefield_factory,
                                     exclude=[f.name
                                                for f in FieldsConfig.get_4_model(model)
                                                                     .hidden_fields
                                             ],
                                    )
                   )
