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

import copy
from functools import partial
from json import dumps as json_dump
import logging
from types import GeneratorType
# import warnings

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
# from django.db.models.query import Q
from django.forms import widgets
from django.urls import reverse
from django.utils.translation import ugettext as _, ugettext_lazy, pgettext_lazy, pgettext

from ..utils.date_range import date_range_registry
from ..utils.queries import QSerializer, get_q_from_dict
from ..utils.url import TemplateURLBuilder

logger = logging.getLogger(__name__)


# def widget_render_input(renderer, widget, name, value, context, **kwargs):
#     warnings.warn('creme_core.forms.widgets.widget_render_input() is deprecated.', DeprecationWarning)
#
#     input_attrs = {'class':  ' '.join(['ui-creme-input', context.get('css', '')]),
#                    'widget': context.get('typename', None),
#                   }
#     input_attrs.update(kwargs)
#
#     return renderer(widget, name, value, input_attrs)
#
#
# def widget_render_hidden_input(widget, name, value, context):
#     warnings.warn('creme_core.forms.widgets.widget_render_hidden_input() is deprecated.', DeprecationWarning)
#
#     input_attrs = {'class': ' '.join(['ui-creme-input', context.get('typename')]),
#                    'type':  'hidden',
#                   }
#
#     return widgets.Input.render(widget, name, value, input_attrs)
#
#
# def widget_render_context(typename, attrs, css='', **kwargs):
#     warnings.warn('creme_core.forms.widgets.widget_render_context() is deprecated.', DeprecationWarning)
#
#     # todo: other atts are not used ?! (eg: ColorPickerWidget which only passes 'attrs' to widget_render_context())
#     id   = attrs.get('id')
#     auto = attrs.pop('auto', True)
#     css = ' '.join((css, 'ui-creme-widget widget-auto' if auto else 'ui-creme-widget', typename)).strip()
#     context = {'style':      '',
#                'typename':   typename,
#                'css':        css,
#                'auto':       auto,
#                'id':         id,
#               }
#
#     context.update(kwargs)
#
#     return context


# TODO: to be improved....
class DynamicInput(widgets.TextInput):
    def __init__(self, type='text', attrs=None):
        # super(DynamicInput, self).__init__(attrs)
        super().__init__(attrs)
        self.input_type = type

    # TODO: factorise ?
    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-dinput'

        # context = super(DynamicInput, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        final_attrs = context['widget']['attrs']
        css_class = 'ui-creme-input ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else \
                    'ui-creme-input ui-creme-widget '
        final_attrs['class'] = css_class + widget_type
        final_attrs['widget'] = widget_type  # TODO: 'data-creme-widget'

        return context


# TODO ??? DynamicHiddenInput
# class HiddenInput(Input): #from django
#     input_type = 'hidden'
#     is_hidden = True


class EnhancedSelectOptions:
    option_template_name = 'creme_core/forms/widgets/enhanced-option.html'

    class Choice:
        def __init__(self, value, disabled=False, help=u''):
            self.value = value
            self.disabled = disabled
            self.help = help

        def __str__(self):
            return str(self.value)

    def _set_options(self, options):
        if options is None:
            self.options = ()
        elif isinstance(options, GeneratorType):
            self.options = list(options)
        else:
            self.options = options

    def _get_options(self):
        return list(self.options()) if callable(self.options) else self.options

    @property
    def choices(self):
        return self._get_options()

    @choices.setter
    def choices(self, choices):
        self._set_options(choices)

    # def render_label(self, output, label):
    #     warnings.warn('creme_core.forms.widgets.EnhancedSelectOptions.render_label() is deprecated.',
    #                   DeprecationWarning
    #                  )
    #
    #     if not self.label:
    #         return output
    #
    #     return u'<span class="ui-creme-dselectlabel">%s</span>%s' % (self.label, output)


class DynamicSelect(EnhancedSelectOptions, widgets.Select):
    template_name = 'creme_core/forms/widgets/dyn-select.html'

    def __init__(self, attrs=None, options=None, url='', label=None):
        # super(DynamicSelect, self).__init__(attrs, ())
        super().__init__(attrs, ())  # TODO: options or ()
        self.url = url
        self.label = label
        self.from_python = None
        self.choices = options

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-dselect'

        # value = self.from_python(value) if self.from_python is not None else value # TODO ?

        # context = super(DynamicSelect, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        widget_cxt = context['widget']
        widget_cxt['label'] = self.label

        final_attrs = widget_cxt['attrs']
        css_class = 'ui-creme-input ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else \
                    'ui-creme-input ui-creme-widget '
        final_attrs['class'] = css_class + widget_type
        final_attrs['widget'] = widget_type  # TODO: 'data-creme-widget'
        final_attrs['url'] = self.url  # TODO 'data-url'  # TODO: only if set ?

        return context


class DynamicSelectMultiple(EnhancedSelectOptions, widgets.SelectMultiple):
    template_name = 'creme_core/forms/widgets/dyn-select.html'

    def __init__(self, attrs=None, options=None, url='', label=None):
        # super(DynamicSelectMultiple, self).__init__(attrs, ())
        super().__init__(attrs, ())  # TODO: options or ()
        self.url = url
        self.label = label
        self.from_python = None
        self.choices = options

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-dselect'

        # value = self.from_python(value) if self.from_python is not None else value  # TODO ?

        # context = super(DynamicSelectMultiple, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        widget_cxt = context['widget']
        widget_cxt['label'] = self.label

        final_attrs = widget_cxt['attrs']
        css_class = 'ui-creme-input ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else \
                    'ui-creme-input ui-creme-widget '
        final_attrs['class'] = css_class + widget_type
        final_attrs['widget'] = widget_type  # TODO: 'data-creme-widget'
        final_attrs['url'] = self.url  # TODO 'data-url'  # TODO: only if set ?

        return context


class ActionButtonList(widgets.Widget):
    template_name = 'creme_core/forms/widgets/action-button-list.html'

    def __init__(self, delegate, attrs=None, actions=()):
        # super(ActionButtonList, self).__init__(attrs)
        super().__init__(attrs)
        self.delegate = delegate
        self.actions = list(actions)
        self.from_python = None

    def __deepcopy__(self, memo):
        # obj = super(ActionButtonList, self).__deepcopy__(memo)
        obj = super().__deepcopy__(memo)
        obj.actions = copy.deepcopy(self.actions)
        return obj

    def add_action(self, name, label, enabled=True, **kwargs):
        self.actions.append((name, label, enabled, kwargs))
        return self

    def clear_actions(self):
        self.actions.clear()
        return self

    def _get_button_context(self, name, label, enabled, **kwargs):
        if enabled is not None:
            if enabled is False or (callable(enabled) and not enabled()):
                kwargs['disabled'] = True

        title = kwargs.pop('title', label)

        return {
            'name':  name,
            'attrs':  kwargs,
            'label': label,
            'title': title,
        }

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-actionbuttonlist'

        value = self.from_python(value) if self.from_python is not None else value

        # context = super(ActionButtonList, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        widget_cxt = context['widget']
        widget_cxt['class'] = 'ui-creme-widget widget-auto ' + widget_type
        widget_cxt['widget_type'] = widget_type

        widget_cxt['delegate'] = self.delegate.get_context(name=name, value=value, attrs=attrs)['widget']
        widget_cxt['buttons'] = [
            self._get_button_context(name=a_name, label=a_label, enabled=a_enabled, **a_attrs)
                for a_name, a_label, a_enabled, a_attrs in self.actions
        ]

        return context


class PolymorphicInput(widgets.TextInput):
    template_name = 'creme_core/forms/widgets/polymorphic-input.html'

    def __init__(self, attrs=None, key='', *args):
        # super(PolymorphicInput, self).__init__(attrs)
        super().__init__(attrs)
        self.key = key
        self.inputs = []
        self.default_input = None
        self.set_inputs(*args)
        self.from_python = None  # TODO: remove this hack ?

    def set_inputs(self, *args):
        for input in args:
            self.add_input(input.name, input.widget, input.attrs, **input.kwargs)

    def add_dselect(self, name, options=None, attrs=None, **kwargs):
        if isinstance(options, str):
            self.add_input(name, widget=DynamicSelect, attrs=attrs, url=options, **kwargs)
        else:
            self.add_input(name, widget=DynamicSelect, attrs=attrs, options=options, **kwargs)

    def add_input(self, name, widget, attrs=None, **kwargs):
        self.inputs.append((name, widget(attrs=attrs, **kwargs) if isinstance(widget, type) else widget))

    def set_default_input(self, widget, attrs=None, **kwargs):
        self.default_input = widget(attrs=attrs, **kwargs) if isinstance(widget, type) else widget

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-polymorphicselect'

        # value = self.from_python(value) if self.from_python is not None else value # TODO ?
        # context = super(PolymorphicInput, self).get_context(name='', value='', attrs=attrs)
        context = super().get_context(name='', value='', attrs=attrs)
        widget_cxt = context['widget']
        widget_cxt['key'] = self.key

        final_attrs = widget_cxt.pop('attrs')
        css_class = 'ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else 'ui-creme-widget '
        widget_cxt['class'] = css_class + widget_type
        widget_cxt['widget_type'] = widget_type

        final_attrs['class'] = 'ui-creme-input ' + widget_type

        widget_cxt['input'] = widgets.HiddenInput().get_context(name=name, value=value, attrs=final_attrs)['widget']

        widget_cxt['selectors'] = selectors = [
            (w_name, w_input.get_context(name='', value='', attrs=None)['widget'])
                for w_name, w_input in self.inputs
        ]
        if self.default_input:
            selectors.append(
                ('*', self.default_input.get_context(name='', value='', attrs=None)['widget'])
            )

        return context


class DateRangeSelect(widgets.Widget):
    template_name = 'creme_core/forms/widgets/date-range-select.html'

    def __init__(self, attrs=None, choices=None):
        # super(DateRangeSelect, self).__init__(attrs)
        super().__init__(attrs)
        self.choices = choices

    def range_choices(self):
        choices = [('', pgettext_lazy('creme_core-date_range', u'Customized'))]
        choices.extend(date_range_registry.choices())
        return choices

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-daterange-selector'

        # context = super(DateRangeSelect, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        widget_cxt = context['widget']

        final_attrs = widget_cxt['attrs']
        css_class = 'ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else 'ui-creme-widget '
        widget_cxt['class'] = css_class + widget_type
        widget_cxt['widget_type'] = widget_type
        final_attrs['class'] = 'ui-creme-input ' + widget_type

        widget_cxt['type'] = 'hidden'
        widget_cxt['date_format'] = settings.DATE_FORMAT_JS.get(settings.DATE_FORMAT)
        widget_cxt['choices'] = self.range_choices() if self.choices is None else self.choices

        return context


class NullableDateRangeSelect(DateRangeSelect):
    def range_choices(self):
        choices = [('', pgettext_lazy('creme_core-date_range', u'Customized'))]
        choices.extend(date_range_registry.choices(exclude_empty=False))
        return choices


class ChainedInput(widgets.TextInput):
    template_name = 'creme_core/forms/widgets/chained-inputs.html'

    HORIZONTAL = 'hbox'
    VERTICAL = 'vbox'

    def __init__(self, attrs=None, *args):
        # super(ChainedInput, self).__init__(attrs)
        super().__init__(attrs)
        self.inputs = []
        self.set_inputs(*args)
        self.from_python = None  # TODO: remove this hack ?

    def __deepcopy__(self, memo):
        # obj = super(ChainedInput, self).__deepcopy__(memo)
        obj = super().__deepcopy__(memo)
        obj.inputs = copy.deepcopy(self.inputs)
        return obj

    def set_inputs(self, *inputs):
        for input in inputs:
            self.add_input(input.name, input.widget, input.attrs, **input.kwargs)

    def add_dselect(self, name, options=None, attrs=None, **kwargs):
        if isinstance(options, str):
            self.add_input(name, widget=DynamicSelect, attrs=attrs, url=options, **kwargs)
        else:
            self.add_input(name, widget=DynamicSelect, attrs=attrs, options=options, **kwargs)

    def add_input(self, name, widget, attrs=None, **kwargs):
        self.inputs.append((name, widget(attrs=attrs or {}, **kwargs) if callable(widget) else widget))

    # TODO ?
    # def clear(self):
    #     self.inputs[:] = ()

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-chainedselect'

        value = self.from_python(value) if self.from_python is not None else value
        # context = super(ChainedInput, self).get_context(name='', value='', attrs=attrs)
        context = super().get_context(name='', value='', attrs=attrs)
        widget_cxt = context['widget']
        final_attrs = widget_cxt.pop('attrs')

        css_class = 'ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else 'ui-creme-widget '
        widget_cxt['class'] = css_class + widget_type
        widget_cxt['widget_type'] = widget_type

        widget_cxt['direction'] = final_attrs.pop('direction', ChainedInput.HORIZONTAL)
        widget_cxt['reset'] = final_attrs.pop('reset', True)

        final_attrs['class'] = 'ui-creme-input ' + widget_type
        widget_cxt['input'] = widgets.HiddenInput().get_context(name=name, value=value, attrs=final_attrs)['widget']

        widget_cxt['chained'] = [
            (w_name, w_input.get_context(name='', value='', attrs=None)['widget'])
                for w_name, w_input in self.inputs
        ]

        return context


class SelectorList(widgets.TextInput):
    template_name = 'creme_core/forms/widgets/selector-list.html'

    class Action:
        def __init__(self, name, label, enabled=True, **attrs):
            self.name = name
            self.label = label
            self.enabled = enabled
            self.attrs = attrs or {}

        @property
        def enabled(self):
            # TODO: self._enabled() ?
            return self._enabled if callable(self._enabled) else (self._enabled is True)

        @enabled.setter
        def enabled(self, enabled):
            self._enabled = enabled

        @property
        def context(self):
            attrs = dict(self.attrs)

            if not self.enabled:
                attrs['disabled'] = True

            title = attrs.pop('title', self.label)

            return {
                'name':  self.name,
                'label': self.label,
                'attrs': attrs,
                'title': title,
            }

    def __init__(self, selector, attrs=None, enabled=True):
        # super(SelectorList, self).__init__(attrs)
        super().__init__(attrs)
        self.selector = selector
        self.enabled = enabled
        self.actions = [self.Action('add', ugettext_lazy(u'Add'))]
        self.from_python = None  # TODO: remove this hack ?

    def add_action(self, name, label, enabled=True, **kwargs):
        self.actions.append(self.Action(name, label, enabled, **kwargs))
        return self

    def clear_actions(self):
        self.actions[:] = ()
        return self

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-selectorlist'

        value = self.from_python(value) if self.from_python is not None else value

        # context = super(SelectorList, self).get_context(name=name, value=value, attrs=None)
        context = super().get_context(name=name, value=value, attrs=None)
        widget_cxt = context['widget']
        widget_cxt['class'] = 'ui-creme-widget widget-auto ' + widget_type
        widget_cxt['widget_type'] = widget_type

        final_attrs = widget_cxt['attrs']
        widget_cxt['clonelast'] = final_attrs.pop('clonelast', True)
        widget_cxt['enabled'] = self.enabled

        widget_cxt['input'] = widgets.HiddenInput() \
                                     .get_context(name=name, value=value,
                                                  attrs={'class': 'ui-creme-input ' + widget_type},
                                                 )['widget']
        widget_cxt['actions'] = [action.context for action in self.actions]
        widget_cxt['selector'] = self.selector.get_context(name='', value='',
                                                           attrs={'auto': False, 'reset': False},
                                                          )['widget']

        return context


class EntitySelector(widgets.Widget):
    template_name = 'creme_core/forms/widgets/entity-selector.html'

    def __init__(self, content_type=None, attrs=None):
        """ Constructor.
        @param content_type: Template variable which represent the ContentType ID in the URL. Default is '${ctype}'.
        @param attrs: see Widget.
        """
        # super(EntitySelector, self).__init__(attrs)
        super().__init__(attrs)
        self.url = self._build_listview_url(content_type)
        self.text_url = self._build_text_url()
        self.from_python = None

    def _build_listview_url(self, content_type):
        return '%s?ct_id=%s&selection=${selection}&q_filter=${qfilter}' % (
            reverse('creme_core__listview_popup'),
            content_type or '${ctype}',
        )

    def _build_text_url(self):
        # TODO: use a GET parameter instead of using a TemplateURLBuilder ?
        return TemplateURLBuilder(entity_id=(TemplateURLBuilder.Int, '${id}'))\
                                 .resolve('creme_core__entity_as_json')

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-entityselector'

        # value = self.from_python(value) if self.from_python is not None else value  # TODO ?

        # context = super(EntitySelector, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        widget_cxt = context['widget']
        widget_cxt['url']      = self.url
        widget_cxt['text_url'] = self.text_url

        final_attrs = widget_cxt['attrs']
        css_class = 'ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else 'ui-creme-widget '
        widget_cxt['class'] = css_class + widget_type
        widget_cxt['widget_type'] = widget_type

        widget_cxt['selection'] = 'multiple' if final_attrs.pop('multiple', False) else 'single'
        widget_cxt['autoselect'] = final_attrs.pop('autoselect', False)
        widget_cxt['disabled']   = final_attrs.pop('disabled', False)

        qfilter = final_attrs.pop('qfilter', None)
        # TODO: factorise (see CreatorEntityField.q_filter_query() )
        if callable(qfilter):
            qfilter = qfilter()
        # if isinstance(qfilter, Q):
        #     raise TypeError('<{}>: "Q" instance for qfilter is not (yet) supported (notice that it '
        #                     'can be generated from the "limit_choices_to" in a field related '
        #                     'to CremeEntity of one of your models).\n'
        #                     ' -> Use a dict (or a callable which returns a dict)'.format(self.__class__.__name__)
        #                    )
        if isinstance(qfilter, dict):
            qfilter = get_q_from_dict(qfilter)

        # widget_cxt['qfilter'] = qfilter
        widget_cxt['qfilter'] = QSerializer().serialize(qfilter) if qfilter else None
        widget_cxt['input'] = widgets.HiddenInput().get_context(name=name, value=value,
                                                                attrs={'class': 'ui-creme-input ' + widget_type},
                                                               )['widget']

        return context


class CTEntitySelector(ChainedInput):
    # template_name = ... TODO in order to override from apps ?

    def __init__(self, content_types=(), attrs=None, multiple=False, autocomplete=False, creator=False):
        # super(CTEntitySelector, self).__init__(attrs)
        super().__init__(attrs)
        self.content_types = content_types
        self.multiple = multiple
        self.autocomplete = autocomplete
        self.creator = creator

    def get_context(self, name, value, attrs):
        field_attrs = {'auto': False, 'datatype': 'json'}
        if self.autocomplete:
            field_attrs['autocomplete'] = True

        self.add_dselect('ctype', options=self.content_types, attrs=field_attrs)

        multiple = self.multiple
        actions = ActionButtonList(delegate=EntitySelector(content_type='${ctype.id}',
                                                           attrs={'auto':     False,
                                                                  'multiple': multiple,
                                                                 },
                                                          ),
                                  )

        if not self.is_required and not multiple:
            clear_label = _(u'Clear')
            actions.add_action('reset', clear_label, title=clear_label,
                               action='reset', value='',
                              )

        if self.creator:
            actions.add_action(name='create', label=_(u'Add'),
                               popupUrl='${ctype.create}', popupTitle='${ctype.create_label}',
                              )

        self.add_input('entity', widget=actions)

        # return super(CTEntitySelector, self).get_context(name=name, value=value, attrs=attrs)
        return super().get_context(name=name, value=value, attrs=attrs)


class MultiCTEntitySelector(SelectorList):
    # template_name = ... TODO in order to override from apps ?

    def __init__(self, content_types=(), attrs=None, autocomplete=False, creator=False):
        # super(MultiCTEntitySelector, self).__init__(None, attrs=attrs)
        super().__init__(None, attrs=attrs)
        self.content_types = content_types
        self.autocomplete = autocomplete
        self.creator = creator

    def get_context(self, name, value, attrs):
        self.selector = CTEntitySelector(content_types=self.content_types,
                                         multiple=True,
                                         autocomplete=self.autocomplete,
                                         creator=self.creator,
                                         attrs={'reset': False},
                                        )

        # return super(MultiCTEntitySelector, self).get_context(name=name, value=value, attrs=attrs)
        return super().get_context(name=name, value=value, attrs=attrs)


class RelationSelector(ChainedInput):
    # template_name = ... TODO in order to override from apps ?

    def __init__(self, relation_types=(), content_types=None,  # TODO: rename 'ctypes_url' ?
                 attrs=None, multiple=False, autocomplete=False,
                ):
        # super(RelationSelector, self).__init__(attrs)
        super().__init__(attrs)
        self.relation_types = relation_types
        self.content_types = content_types
        self.multiple = multiple
        self.autocomplete = autocomplete

    def _build_ctypes_url(self):
        return TemplateURLBuilder(rtype_id=(TemplateURLBuilder.Word, '${rtype}'))\
                                 .resolve('creme_core__ctypes_compatible_with_rtype')

    def get_context(self, name, value, attrs):
        dselect_attrs = {'auto': False, 'autocomplete': True} if self.autocomplete else \
                        {'auto': False}

        self.add_dselect('rtype', options=self.relation_types, attrs=dselect_attrs)
        self.add_dselect('ctype', options=self.content_types or self._build_ctypes_url(), attrs=dselect_attrs)
        self.add_input('entity', widget=EntitySelector,
                       attrs={'auto': False, 'multiple': self.multiple},
                      )

        # return super(RelationSelector, self).get_context(name=name, value=value, attrs=attrs)
        return super().get_context(name=name, value=value, attrs=attrs)


class MultiRelationSelector(SelectorList):
    # template_name = ... TODO in order to override from apps ?

    def __init__(self, relation_types=(), content_types=None,
                 attrs=None, autocomplete=False,
                ):
        # super(MultiRelationSelector, self).__init__(None, attrs=attrs)
        super().__init__(None, attrs=attrs)
        self.relation_types = relation_types
        self.content_types = content_types
        self.autocomplete = autocomplete

    def get_context(self, name, value, attrs):
        self.selector = RelationSelector(relation_types=self.relation_types,
                                         content_types=self.content_types,
                                         multiple=True,
                                         autocomplete=self.autocomplete,
                                        )

        # return super(MultiRelationSelector, self).get_context(name=name, value=value, attrs=attrs)
        return super().get_context(name=name, value=value, attrs=attrs)


class EntityCreatorWidget(ActionButtonList):
    # template_name = ... TODO in order to override from apps ?

    def __init__(self, model=None, q_filter=None, attrs=None, creation_url='', creation_allowed=False):
        # super(EntityCreatorWidget, self).__init__(delegate=None, attrs=attrs)
        super().__init__(delegate=None, attrs=attrs)
        self.model = model
        self.q_filter = q_filter
        self.creation_url = creation_url
        self.creation_allowed = creation_allowed

    def _is_disabled(self, attrs):
        if attrs is not None:
            return 'disabled' in attrs or 'readonly' in attrs

        return False

    def _build_actions(self, model, attrs):
        is_disabled = self._is_disabled(attrs)

        self.clear_actions()

        if not is_disabled:
            if not self.is_required:
                clear_label = _(u'Clear')
                self.add_action('reset', clear_label, title=clear_label, action='reset', value='')

            url = self.creation_url

            if url:
                allowed = self.creation_allowed
                self.add_action('create', model.creation_label, enabled=allowed, popupUrl=url,
                                title=_(u'Create') if allowed else _(u"Can't create"),
                               )

    def get_context(self, name, value, attrs):
        model = self.model

        # TODO: creating instance of delegate here is ugly (use an ActionButtonList & not inherit it ?)
        if model is None:
            self.delegate = Label(empty_label='Model is not set')
        else:
            selector_attrs = {'auto': False, 'disabled': self._is_disabled(attrs)}

            if self.q_filter is not None:
                selector_attrs['qfilter'] = self.q_filter

            self.delegate = EntitySelector(
                str(ContentType.objects.get_for_model(model).id),
                selector_attrs,
            )

            self._build_actions(model, attrs)

        # return super(EntityCreatorWidget, self).get_context(name=name, value=value, attrs=attrs)
        return super().get_context(name=name, value=value, attrs=attrs)


# TODO: factorise with EntityCreatorWidget ?
class MultiEntityCreatorWidget(SelectorList):
    # template_name = ... TODO in order to override from apps ?

    def __init__(self, model=None, q_filter=None, attrs=None, creation_url='', creation_allowed=False):
        attrs = attrs or {'clonelast': False}
        # super(MultiEntityCreatorWidget, self).__init__(None, attrs=attrs)
        super().__init__(None, attrs=attrs)
        self.model = model
        self.q_filter = q_filter
        self.creation_url = creation_url
        self.creation_allowed = creation_allowed

    def get_context(self, name, value, attrs):
        model = self.model
        self.selector = button_list = ActionButtonList(delegate=None)  # TODO: create only if does not exist ?

        if model is None:
            delegate = Label(empty_label='Model is not set')
        else:
            self.clear_actions()  # TODO: indicate that we do not want actions in __init__
            self.add_action('add', getattr(model, 'selection_label', pgettext('creme_core-verb', u'Select')))

            delegate = EntitySelector(str(ContentType.objects.get_for_model(model).id),
                                      {'auto':       False,
                                       'qfilter':    self.q_filter,
                                       'multiple':   True,
                                       'autoselect': True,
                                      },
                                     )

            def add_action(name, label, enabled=True, **kwargs):
                button_list.add_action(name, label, enabled=False, hidden=True, **kwargs)
                self.add_action(name, label, enabled)

            url = self.creation_url
            if url:
                allowed = self.creation_allowed
                add_action('create', model.creation_label, enabled=allowed, popupUrl=url,
                           title=_(u'Create') if allowed else _(u"Can't create")
                          )

        button_list.delegate = delegate

        # return super(MultiEntityCreatorWidget, self).get_context(name=name, value=value, attrs=attrs)
        return super().get_context(name=name, value=value, attrs=attrs)


class FilteredEntityTypeWidget(ChainedInput):
    # template_name = ... TODO in order to override from apps ?

    def __init__(self, content_types=(), attrs=None, autocomplete=True):
        # super(FilteredEntityTypeWidget, self).__init__(attrs)
        super().__init__(attrs)
        self.content_types = content_types
        self.autocomplete = autocomplete

    def get_context(self, name, value, attrs):
        add_dselect = partial(self.add_dselect,
                              attrs={'auto': False, 'autocomplete': self.autocomplete},
                             )
        ctype_name = 'ctype'
        add_dselect(ctype_name, options=self.content_types)

        # TODO: allow to omit the 'All' filter ??
        # TODO: do not make a request for ContentType ID == '0'
        add_dselect('efilter',
                    options=reverse('creme_core__efilters') + '?ct_id=${%s}&all=true' % ctype_name,
                   )

        # return super(FilteredEntityTypeWidget, self).get_context(name=name, value=value, attrs=attrs)
        return super().get_context(name=name, value=value, attrs=attrs)


class DateTimeWidget(widgets.DateTimeInput):
    is_localized = True
    template_name = 'creme_core/forms/widgets/datetime.html'

    def __init__(self, attrs=None):
        # super(DateTimeWidget, self).__init__(attrs=attrs, format='%d-%m-%Y %H:%M')
        super().__init__(attrs=attrs, format='%d-%m-%Y %H:%M')

    def get_context(self, name, value, attrs):
        # context = super(DateTimeWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        widget_cxt = context['widget']
        widget_cxt['type'] = 'hidden'
        widget_cxt['date_format'] = settings.DATE_FORMAT_JS.get(settings.DATE_FORMAT)

        return context


class TimeWidget(widgets.TextInput):
    template_name = 'creme_core/forms/widgets/time.html'

    def get_context(self, name, value, attrs):
        # context = super(TimeWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        context['widget']['type'] = 'hidden'

        return context

    def value_from_datadict(self, data, files, name):
        value = data.get(name, '')

        if value.strip() == ':':
            value = ''

        return value


class CalendarWidget(widgets.TextInput):
    is_localized = True
    template_name = 'creme_core/forms/widgets/date.html'
    default_help_text = settings.DATE_FORMAT_VERBOSE

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-datepicker'

        # context = super(CalendarWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        widget_cxt = context['widget']
        widget_cxt['format_help_text'] = self.default_help_text

        final_attrs = widget_cxt['attrs']

        css_class = 'ui-creme-input ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else \
                    'ui-creme-input ui-creme-widget '
        final_attrs['class'] = css_class + widget_type
        final_attrs['widget'] = widget_type  # TODO: data-widget-type
        final_attrs['format'] = settings.DATE_FORMAT_JS.get(settings.DATE_FORMAT)  # TODO: data-date-format

        return context


# TODO: Only used in reports for now. Kept until *Selector widgets accept optgroup
class DependentSelect(widgets.Select):
    template_name = 'creme_core/forms/widgets/dependent-select.html'

    def __init__(self, target_id, attrs=None, choices=()):
        self.target_id = target_id
        self.target_url = None
        self.target_val = None
        # super(DependentSelect, self).__init__(attrs, choices)
        super().__init__(attrs, choices)

    def get_context(self, name, value, attrs):
        # context = super(DependentSelect, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        final_attrs = context['widget']['attrs']
        final_attrs['onchange'] = """(function() {
    var source = $('#%(id)s');
    if (!source || typeof(source) === undefined) return;

    var target = $('#%(target_id)s');
    if (!target || typeof(target) === undefined) return;

    $.post('%(target_url)s',
           {record_id: source.val()},
           function(data) {
               var data = creme.forms.Select.optionsFromData(data.result, 'text', 'id');
               creme.forms.Select.fill(target, data, '%(target_val)s');
           }, 'json');
}());""" % {
            'id': final_attrs['id'],
            'target_id': self.target_id,
            'target_url': self.target_url,
            'target_val': self.target_val,
        }

        return context


class OptionalWidget(widgets.MultiWidget):
    template_name = 'creme_core/forms/widgets/optional.html'

    def __init__(self, sub_widget=widgets.TextInput, attrs=None, sub_label=''):
        # super(OptionalWidget, self).__init__(
        super().__init__(
            widgets=(widgets.CheckboxInput(attrs={'onchange': 'creme.forms.optionalWidgetHandler(this)'}),
                     sub_widget,
                    ),
            attrs=attrs,
        )
        self.sub_label = sub_label

    def decompress(self, value):
        return (value[0], value[1]) if value else (None, None)

    def get_context(self, name, value, attrs):
        # context = super(OptionalWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        context['widget']['label'] = self.sub_label

        return context

    @property
    def sub_widget(self):
        return self.widgets[1]


class OptionalSelect(OptionalWidget):
    def __init__(self, choices=(), *args, **kwargs):
        # super(OptionalSelect, self).__init__(widgets.Select(choices=choices), *args, **kwargs)
        super().__init__(widgets.Select(choices=choices), *args, **kwargs)


class TinyMCEEditor(widgets.Textarea):
    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-jqueryplugin'
        # context = super(TinyMCEEditor, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        final_attrs = context['widget']['attrs']
        css_class = 'ui-creme-input ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else \
                    'ui-creme-input ui-creme-widget '
        final_attrs['class'] = css_class + widget_type
        final_attrs['widget'] = widget_type
        final_attrs['plugin'] = 'tinymce'
        final_attrs['plugin_options'] = json_dump({
            'mode':                            'textareas',
            'script_url':                      '{}tiny_mce/tiny_mce.js'.format(settings.MEDIA_URL),
            'convert_urls':                    False,
            'theme':                           'advanced',
            'height':                          300,
            'plugins':                         "spellchecker,pagebreak,style,layer,table,save,advhr,advimage,advlink,emotions,iespell,inlinepopups,insertdatetime,preview,media,searchreplace,print,contextmenu,paste,directionality,fullscreen,noneditable,visualchars,nonbreaking,xhtmlxtras,template, fullpage",
            'theme_advanced_buttons1':         "save,newdocument,|,bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,|,styleselect,formatselect,fontselect,fontsizeselect",
            'theme_advanced_buttons2':         "cut,copy,paste,pastetext,pasteword,|,search,replace,|,bullist,numlist,|,outdent,indent,blockquote,|,undo,redo,|,link,unlink,anchor,image,cleanup,code,|,insertdate,inserttime,preview,|,forecolor,backcolor",
            'theme_advanced_buttons3':         "tablecontrols,|,hr,removeformat,visualaid,|,sub,sup,|,charmap,emotions,iespell,media,advhr,|,print,|,ltr,rtl,|,fullscreen",
            'theme_advanced_buttons4':         "insertlayer,moveforward,movebackward,absolute,|,styleprops,spellchecker,|,cite,abbr,acronym,del,ins,attribs,|,visualchars,nonbreaking,blockquote,pagebreak,|,insertfile,insertimage",
            'theme_advanced_toolbar_location': 'top',
            'theme_advanced_toolbar_align':    'left',
            'theme_advanced_path_location':    'bottom',
            'theme_advanced_resizing':         True,
        })

        return context


class ColorPickerWidget(widgets.TextInput):
    template_name = 'creme_core/forms/widgets/color.html'

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-jqueryplugin'
        # context = super(ColorPickerWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        final_attrs = context['widget']['attrs']
        css_class = 'ui-creme-input ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else \
                    'ui-creme-input ui-creme-widget '
        final_attrs['class'] = css_class + widget_type
        final_attrs['widget'] = widget_type
        final_attrs['plugin'] = 'gccolor'

        return context


class UnorderedMultipleChoiceWidget(EnhancedSelectOptions, widgets.SelectMultiple):
    template_name = 'creme_core/forms/widgets/unordered-multiple.html'

    MODE_SEARCH = 'search'
    MODE_FILTER = 'filter'
    MODES = {MODE_SEARCH, MODE_FILTER}

    MIN_SEARCH_COUNT = 10
    MIN_FILTER_COUNT = 30
    MIN_CHECKALL_COUNT = 3

    def __init__(self, attrs=None, choices=(),
                 columntype='', filtertype=None, viewless=20,  # viewless=None,
                 creation_url='', creation_allowed=False, creation_label=ugettext_lazy(u'Create')):
        """Constructor.
        @param attrs: See SelectMultiple.attrs.
        @param choices: See SelectMultiple.choices.
        @param columntype: Extra CSS class of the items container.
        @param filtertype: 'search' to activate search mode (items which do not match are translucent) ;
                           'filter' to activate filter mode (items which do not match are hidden) ;
                           Empty to let the widget chose the mode.
        @param viewless: An integer N to hide the items after the Nth item ;
                         True to let the widget chose the value of N ;
                         False to deactivate this "less" feature.
        @param creation_url: URL to create a new element (in an inner-popup dialog) ; ignored if empty.
        @param creation_allowed: False to disable the creation button (only used if 'creation_url' is given).
        @param creation_label: Label of the creation button (only used if 'creation_url' is given).
        """
        # super(UnorderedMultipleChoiceWidget, self).__init__(attrs, choices)
        super().__init__(attrs, choices)
        self.columntype = columntype
        self.filtertype = filtertype
        self.viewless = viewless
        self.creation_url = creation_url
        self.creation_allowed = creation_allowed
        self.creation_label = creation_label

    def _choice_count(self):  # TODO: inline ?
        return sum(len(c[1]) if isinstance(c[1], (list, tuple)) else 1 for c in self.choices)

    def _build_filtertype(self, count):
        if self._filtertype:
            return self._filtertype

        if count < self.MIN_SEARCH_COUNT:
            return None
        elif count < self.MIN_FILTER_COUNT:
            return self.MODE_SEARCH
        else:
            return self.MODE_FILTER

    @property
    def filtertype(self):
        return self._filtertype

    @filtertype.setter
    def filtertype(self, filtertype):
        if filtertype and filtertype not in self.MODES:
            raise ValueError('UnorderedMultipleChoiceWidget.filtertype: the value must be in {expected} '
                             '(given value: "{value}")'.format(expected=self.MODES, value=filtertype)
                            )

        self._filtertype = filtertype

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-checklistselect'

        if value is not None:
            value = list(value)

        count = self._choice_count()
        # context = super(UnorderedMultipleChoiceWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        widget_cxt = context['widget']

        final_attrs = widget_cxt['attrs']
        css_class = 'ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else 'ui-creme-widget '
        widget_cxt['class'] = css_class + widget_type
        final_attrs['class'] = 'ui-creme-input'
        widget_cxt['widget_type'] = widget_type

        widget_cxt['column_type'] = self.columntype
        widget_cxt['view_less'] = self.viewless

        widget_cxt['checkall'] = final_attrs.pop('checkall', True)

        widget_cxt['choice_count'] = count
        widget_cxt['filter_type'] = self._build_filtertype(count)

        widget_cxt['MIN_CHECKALL_COUNT'] = self.MIN_CHECKALL_COUNT
        widget_cxt['MIN_SEARCH_COUNT']   = self.MIN_SEARCH_COUNT  # NB: not used ; set for consistency/extensibility.
        widget_cxt['MIN_FILTER_COUNT']   = self.MIN_FILTER_COUNT  # Idem

        widget_cxt['creation_allowed'] = self.creation_allowed
        widget_cxt['creation_url']     = self.creation_url
        widget_cxt['creation_label']   = self.creation_label

        return context


class OrderedMultipleChoiceWidget(widgets.SelectMultiple):
    template_name = 'creme_core/forms/widgets/ordered-multiple.html'

    def get_context(self, name, value, attrs):
        # context = super(OrderedMultipleChoiceWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        context['widget']['orders'] = {
            opt_value: order + 1
                for order, opt_value in enumerate(value or ())
        }

        return context

    def value_from_datadict(self, data, files, name):
        prefix_check = '{}_check_'.format(name)
        prefix_order = '{}_order_'.format(name)
        prefix_value = '{}_value_'.format(name)

        selected = []
        for key, value in data.items():
            if key.startswith(prefix_check):
                index = key[len(prefix_check):]  # In fact not an int...
                order = int(data.get(prefix_order + index) or 0)
                value = data[prefix_value + index]
                selected.append((order, value))

        selected.sort(key=lambda i: i[0])

        return [val for _order, val in selected]


class Label(widgets.TextInput):
    template_name = 'creme_core/forms/widgets/label.html'
    empty_label = None  # TODO: remove ?

    def __init__(self, attrs=None, empty_label=None):
        # super(Label, self).__init__(attrs=attrs)
        super().__init__(attrs=attrs)
        self.empty_label = empty_label

    def get_context(self, name, value, attrs):
        # context = super(Label, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)
        context['widget']['content'] = value or self.empty_label

        return context


class ListEditionWidget(widgets.Widget):
    template_name = 'creme_core/forms/widgets/list-editor.html'
    content = ()
    only_delete = False

    def get_context(self, name, value, attrs):
        # context = super(ListEditionWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        items = []
        for i, label in enumerate(self.content):
            checked = True

            if value:
                new_label = value[i]

                if new_label is None:
                    checked = False
                else:
                    label = new_label

            items.append({'checked': checked, 'label': label})

        widget_ctxt = context['widget']
        widget_ctxt['only_delete'] = self.only_delete
        widget_ctxt['items'] = items

        return context

    def value_from_datadict(self, data, files, name):
        prefix_check_fmt = (name + '_check_{}').format
        prefix_value_fmt = (name + '_value_{}').format
        get = data.get
        # has_key = data.has_key

        # return [get(prefix_value_fmt(i)) if has_key(prefix_check_fmt(i)) else None
        return [get(prefix_value_fmt(i)) if (prefix_check_fmt(i) in data) else None
                    for i in range(len(self.content))
               ]


class DatePeriodWidget(widgets.MultiWidget):
    template_name = 'creme_core/forms/widgets/date-period.html'

    def __init__(self, choices=(), attrs=None):
        # super(DatePeriodWidget, self).__init__(
        super().__init__(
            widgets=(widgets.Select(choices=choices, attrs={'class': 'dperiod-type'}),
                     widgets.TextInput(attrs={'class': 'dperiod-value'}),  # TODO: min_value
                    ),
            attrs=attrs,
        )

    @property
    def choices(self):
        return self.widgets[0].choices

    @choices.setter
    def choices(self, choices):
        self.widgets[0].choices = choices

    def decompress(self, value):
        if value:
            d = value.as_dict()
            return d['type'], d['value']

        return None, None

    def get_context(self, name, value, attrs):
        # context = super(DatePeriodWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        # TODO: do we need a system for localized settings (like python in locale/ ) ?
        try:
            localized_order = _(u'{dateperiod_value}{dateperiod_type}').format(
                dateperiod_type='0',
                dateperiod_value='1',
            )
            inverted = localized_order.index('1') < localized_order.index('0')
        except:
            logger.exception('DatePeriodWidget.get_context()')
            inverted = False

        context['widget_indices'] = (1, 0) if inverted else (0, 1)

        return context


class DateRangeWidget(widgets.MultiWidget):
    template_name_format = 'creme_core/forms/widgets/date-range/{}.html'

    def __init__(self, choices=(), attrs=None):
        self.render_as = attrs.pop('render_as', 'table') if attrs else 'table'

        # super(DateRangeWidget, self).__init__(
        super().__init__(
            widgets=(widgets.Select(choices=choices, attrs={'data-daterange-type': True}),
                     CalendarWidget(attrs={'data-daterange-field': 'start'}),
                     CalendarWidget(attrs={'data-daterange-field': 'end'}),
                    ),
            attrs=attrs,
        )

    @property
    def choices(self):
        return self.widgets[0].choices

    @choices.setter
    def choices(self, choices):
        self.widgets[0].choices = choices

    def decompress(self, value):
        if value:
            return value[0], value[1], value[2]
        return None, None, None

    @property
    def template_name(self):
        return self.template_name_format.format(self.render_as)

    def get_context(self, name, value, attrs):
        widget_type = 'ui-creme-daterange'
        # context = super(DateRangeWidget, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        widget_cxt = context['widget']
        final_attrs = widget_cxt['attrs']
        css_class = 'ui-creme-widget widget-auto ' if final_attrs.pop('auto', True) else 'ui-creme-widget '
        widget_cxt['class'] = css_class + widget_type
        widget_cxt['widget_type'] = widget_type

        return context


class DurationWidget(widgets.MultiWidget):
    template_name = 'creme_core/forms/widgets/duration.html'

    def __init__(self, attrs=None):
        TextInput = widgets.TextInput
        # super(DurationWidget, self).__init__(widgets=[TextInput] * 3,
        #                                      attrs=attrs,
        #                                     )
        super().__init__(widgets=[TextInput] * 3, attrs=attrs)

    def decompress(self, value):
        return value.split(':') if value else (None, None, None)


class ChoiceOrCharWidget(widgets.MultiWidget):
    def __init__(self, attrs=None, choices=()):
        # super(ChoiceOrCharWidget, self).__init__(
        super().__init__(
            widgets=(widgets.Select(choices=choices), widgets.TextInput()),
            attrs=attrs,
        )

    @property
    def choices(self):
        return self.widgets[0].choices

    @choices.setter
    def choices(self, choices):
        self.widgets[0].choices = choices

    def decompress(self, value):
        if value:
            return value[0], value[1]

        return None, None


class CremeRadioSelect(widgets.RadioSelect):
    template_name = 'creme_core/forms/widgets/radio.html'

    def get_context(self, name, value, attrs):
        # context = super(CremeRadioSelect, self).get_context(name=name, value=value, attrs=attrs)
        context = super().get_context(name=name, value=value, attrs=attrs)

        final_attrs = context['widget']['attrs']
        final_attrs['class'] = '{} {}'.format(final_attrs.get('class', ''), 'radio_select').strip()

        return context
