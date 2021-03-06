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

import logging
import warnings

from itertools import zip_longest
from json import dumps as json_dump
from re import compile as compile_re
from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Template, TemplateSyntaxError, Node as TemplateNode
from django.template.defaulttags import TemplateLiteral
from django.template.library import token_kwargs
from django.utils.encoding import force_text
from django.utils.html import format_html_join, escape
from django.utils.safestring import mark_safe

from mediagenerator.generators.bundles.utils import _render_include_media

from ..backends import import_backend_registry, export_backend_registry
from ..gui.field_printers import field_printers_registry
from ..models import CremeEntity, Relation
from ..utils import bool_as_html  # safe_unicode
from ..utils.currency_format import currency
from ..utils.html import escapejson 
from ..utils.media import get_creme_media_url
from ..utils.serializers import json_encode
from ..utils.translation import plural
from ..utils.unicode_collation import collator


logger = logging.getLogger(__name__)
register = Library()


@register.filter(name='print_boolean')
def print_boolean(x):
    return bool_as_html(x)


@register.filter
def get_by_index(sequence, index):
    """Get the Nth item in a sequence (index can be a context variable).
    Context:
       my_list=['a', 'b', 'c']
       my_idx=1
    Template:
      {{my_list|get_by_index:my_idx}}{# Displays 'b' #}
    """
    return sequence[index]


@register.filter
def get_value(dic, key, default=''):
    """Get a a value from its key in a dictionary-like object, with a default
    value as fallback (ie: like dict.get())

    Usage:
      View (context):
          some_dict = {'keyA': 'valueA',
                       'keyB': {'subKeyA': 'subValueA', 'subKeyB': 'subKeyB'},
                       'keyC': 'valueC',
                      }
          keys = ['keyA','keyC']

      Template:
          {{ some_dict|get_value:"keyA" }}
          {{ some_dict|get_value:"keyB"|get_value:"subKeyA" }}
          {% for key in keys %}{{ some_dict|get_value:key }}{% endfor %}
    """
    try:
        return dic.get(key, default)
    except Exception as e:  # TODO: really useful ???
        logger.debug('Exception in get_value(): %s', e)
        return default


@register.filter
def get_meta_value(obj, key, default=''):
    try:
        return getattr(obj._meta, key)
    except AttributeError as e:
        logger.warning('Templatetag get_meta_value: %s', e)
    except:
        pass

    return default


@register.filter(name='get_tag')
def get_fieldtag(field, tag):
    """eg: {% if field|get_tag:'viewable' %}"""
    warnings.warn('"my_field|get_tag:"my_tag" is deprecated.', DeprecationWarning)

    return field.get_tag(tag)


@register.simple_tag
def get_field_verbose_name(model_or_entity, field_name):
    warnings.warn('{% get_field_verbose_name %} is deprecated ; '
                  'use {% cell_4_regularfield %} from lib "creme_cells" instead.',
                  DeprecationWarning
                 )

    from django.db.models import FieldDoesNotExist
    from ..utils.meta import FieldInfo

    try:
        return FieldInfo(model_or_entity, field_name).verbose_name
    except FieldDoesNotExist as e:
        logger.debug('Exception in get_field_verbose_name(): %s', e)
        return 'INVALID FIELD'


@register.simple_tag(takes_context=True)
def get_viewable_fields(context, instance):
    warnings.warn('{% get_viewable_fields %} is deprecated.', DeprecationWarning)

    is_hidden = context['fields_configs'].get_4_model(instance.__class__).is_field_hidden

    return [field
                for field in instance._meta.fields
                    if field.get_tag('viewable') and not is_hidden(field)
           ]


_log_levels = {
    'CRITICAL': logging.CRITICAL,
    'ERROR':    logging.ERROR,
    'WARN':     logging.WARNING,
    'INFO':     logging.INFO,
    'DEBUG':    logging.DEBUG,
}

@register.simple_tag
def log(msg, level='INFO'):
    logger.log(_log_levels.get(level, logging.INFO), msg)
    return ''


# TODO: 'o|is_op:None' instead ?
@register.filter
def is_none(obj):
    return obj is None


# TODO: replace by a filter 'ctype_is' in creme_ctype.py ?
@register.filter
def is_entity(obj):
    return isinstance(obj, CremeEntity)


@register.filter
def is_relation(obj):
    return isinstance(obj, Relation)


@register.filter(name='lt')
def lt(x, y):
    return x < y


@register.filter(name='gt')
def gt(x, y):
    return x > y


@register.filter(name='lte')
def lte(x, y):
    return x <= y


@register.filter(name='gte')
def gte(x, y):
    return x >= y


@register.filter(name='eq')
def eq(x, y):
    return x == y


@register.filter
def and_op(object1, object2):
    return object1 and object2


@register.filter
def or_op(object1, object2):
    return object1 or object2


@register.filter(name='bool')
def _bool(object1):
    return bool(object1)


@register.filter(name='str')
def _str(object1):
    return str(object1)


# NB: 'abs' name gives a template syntax error
@register.filter
def absolute(integer):
    return abs(integer)


@register.filter(name='in')
def in_list(obj, sequence):
    return obj in sequence


# NB: |add is provided by Django
@register.filter
def sub(x, y):
    return x - y


@register.filter
def mult(x, y):
    return x * y


@register.filter
def idiv(integer1, integer2):
    # return integer1 / integer2
    return integer1 // integer2


# TODO ?
# @register.filter
# def div(x, y):
#     return x / y


@register.filter
def mod(integer1, integer2):
    return integer1 % integer2


@register.filter(name='xrange')
def x_range(integer, start=0):
    warnings.warn('The template filter "|xrange" is deprecated ; use "|range" instead.', DeprecationWarning)

    return range(start, start + integer)


@register.filter(name='range')
def range_filter(integer, start=0):
    return range(start, start + integer)


@register.filter
def isiterable(iterable):  # TODO: rename is_iterable for consistency
    return hasattr(iterable, '__iter__')


@register.filter
def is_plural(x):
    return plural(x)


@register.filter(name='format')
def format_string(ustring, format_str):
    return format_str % ustring


# NB: seems not used any more...
@register.filter
def to_timestamp(date):
    return date.strftime('%s')


@register.filter
def uca_sort(iterable):
    strs = [str(e) for e in iterable]
    strs.sort(key=collator.sort_key)

    return strs


@register.filter
def allowed_unicode(entity, user):
    warnings.warn('The template filter "|allowed_unicode" is deprecated ; use "|allowed_str" instead.',
                  DeprecationWarning
                 )

    return entity.allowed_unicode(user)


# NB: really useful ? {% widget_entity_hyperlink %} seems always used instead...
@register.filter
def allowed_str(entity, user):
    return entity.allowed_str(user)


@register.filter
def format_amount(amount, currency_or_id=None):
    return currency(amount, currency_or_id)


@register.filter
def optionize_model_iterable(iterable, type='tuple'):
    if type == 'dict':
        # return ({'value': model.id, 'label': safe_unicode(model)} for model in iterable)
        return ({'value': model.id, 'label': str(model)} for model in iterable)
    else:
        # return ((model.id, safe_unicode(model)) for model in iterable)
        return ((model.id, str(model)) for model in iterable)


@register.filter
def jsonify(value):
    return json_encode(value)


@register.simple_tag
def jsondata(value, **kwargs):
    """ Encode and render json data in a <script> tag with attributes.

    {% jsondata data arg1=foo.bar arg2='baz' %}
    """
    if value is None:
        return ''

    if kwargs.pop("type", None) is not None:
        logger.warning('jsondata tag do not accept custom "type" attribute')

    content = jsonify(value) if not isinstance(value, str) else value
    attrs = ''.join(' {}="{}"'.format(k, escape(v)) for k, v in kwargs.items())

    return mark_safe('<script type="application/json"{}><!-- {} --></script>'.format(attrs, escapejson(content)))


# TODO: useless ?
@register.simple_tag
def get_entity_summary(entity, user):
    return entity.get_entity_summary(user)


@register.simple_tag(takes_context=True)
def get_entity_html_attrs(context, entity):
    return format_html_join(' ', '{}="{}"', entity.get_html_attrs(context).items())


# See grouper implementation: https://docs.python.org/2/library/itertools.html#recipes
@register.filter
def grouper(value, n):
    args = [iter(value)] * n
    return zip_longest(fillvalue=None, *args)


@register.simple_tag
def url_join(*args, **params):
    """ Add some GET parameters to a URL.
    It's work even if the URL has already some GET parameters.

    {% url_join my_url arg1=foo.bar arg2='baz' as my_uri %}
    """
    if not args:
        return ''

    # NB: we take the base URL with *args in order to allow all values for GET keys.
    if len(args) > 1:
        raise TemplateSyntaxError('url_join takes one & only one positional argument (the base URL)')

    base = args[0]

    if not base:
        return ''
    # TODO: base = str(base) ?

    if not params:
        uri = base
    elif urlsplit(base).query:  # There are already some GET params
        uri = base + '&' + urlencode(params, doseq=True)
    else:
        uri = base + '?' + urlencode(params, doseq=True)

    return mark_safe(uri)


# TAG : "templatize"------------------------------------------------------------
_templatize_re = compile_re(r'(.*?) as (\w+)')


@register.tag(name='templatize')
def do_templatize(parser, token):
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError as e:
        raise TemplateSyntaxError('{!r} tag requires arguments'.format(token.contents.split()[0])) from e

    match = _templatize_re.search(arg)
    if not match:
        raise TemplateSyntaxError('{!r} tag had invalid arguments: {!r}'.format(tag_name, arg))

    template_string, var_name = match.groups()

    first_char = template_string[0]
    if not (first_char == template_string[-1] and first_char in {'"', "'"}):
        raise TemplateSyntaxError("{!r} tag's argument should be in quotes".format(tag_name))

    return TemplatizeNode(template_string[1:-1], var_name)


class TemplatizeNode(TemplateNode):
    def __init__(self, template_string, var_name):
        self.inner_template = Template(template_string)
        self.var_name = var_name

    def __repr__(self):
        return "<Templatize node>"

    def render(self, context):
        context[self.var_name] = self.inner_template.render(context)
        return ''


# TAG : "print_field"-----------------------------------------------------------
_PRINT_FIELD_RE = compile_re(r'object=(.*?) field=(.*?)$')


@register.tag(name='print_field')
def do_print_field(parser, token):
    """Eg:{% print_field object=object field='created' %}"""
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError as e:
        raise TemplateSyntaxError("{!r} tag requires arguments".format(token.contents.split()[0])) from e

    match = _PRINT_FIELD_RE.search(arg)
    if not match:
        raise TemplateSyntaxError("{!r} tag had invalid arguments".format(tag_name))

    obj_str, field_str = match.groups()
    compile_filter = parser.compile_filter

    return FieldPrinterNode(obj_var=TemplateLiteral(compile_filter(obj_str), obj_str),
                            field_var=TemplateLiteral(compile_filter(field_str), field_str),
                           )


class FieldPrinterNode(TemplateNode):
    def __init__(self, obj_var, field_var):
        self.obj_var = obj_var
        self.field_var = field_var

    def render(self, context):
        obj        = self.obj_var.eval(context)
        field_name = self.field_var.eval(context)

        # TODO: pass the registry in the context ?
        return field_printers_registry.get_html_field_value(obj, field_name, context['user'])


# TAG : "has_perm_to"-----------------------------------------------------------

# TODO: move to a 'creme_auth' file ??
_haspermto_re = compile_re(r'(\w+) (.*?) as (\w+)')


def _can_create(model_or_ct, user):
    ct = model_or_ct if isinstance(model_or_ct, ContentType) else ContentType.objects.get_for_model(model_or_ct)
    return user.has_perm('{}.add_{}'.format(ct.app_label, ct.model))
    # return user.has_perm_to_create(ct) #TODO + had the possibility to pass CT directly


def _can_export(model_or_ct, user):
    ct = model_or_ct if isinstance(model_or_ct, ContentType) else ContentType.objects.get_for_model(model_or_ct)
    return user.has_perm('{}.export_{}'.format(ct.app_label, ct.model))
    # return user.has_perm_to_export(ct) #TODO ?

_PERMS_FUNCS = {
        'create': _can_create,
        'export': _can_export,
        'view':   lambda entity, user: user.has_perm_to_view(entity),
        'change': lambda entity, user: user.has_perm_to_change(entity),
        'delete': lambda entity, user: user.has_perm_to_delete(entity),
        'link':   lambda entity_or_model, user: user.has_perm_to_link(entity_or_model),  # TODO: or ctype
        'unlink': lambda entity, user: user.has_perm_to_unlink(entity),
        'access': lambda app_name, user: user.has_perm_to_access(app_name),
        'admin':  lambda app_name, user: user.has_perm_to_admin(app_name),
    }


@register.tag(name='has_perm_to')
def do_has_perm_to(parser, token):
    """{% has_perm_to TYPE OBJECT as VAR %}
    eg: {% has_perm_to change action.creme_entity as has_perm %}

    TYPE: must be in ('create', 'view','change', 'delete', 'link', 'unlink', 'create', 'export', 'admin')
    OBJECT: * TYPE in ('view','change', 'delete', 'unlink') => must be a CremeEntity.
            * TYPE='link' => can be a CremeEntity instance or a class inheriting from CremeEntity.
            * TYPE in ('create', 'export') and a class inheriting from CremeEntity OR a ContentType instance.
            * TYPE='admin' => an app name, like 'creme_core'.
    """
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError as e:
        raise TemplateSyntaxError('{!r} tag requires arguments'.format(token.contents.split()[0])) from e

    match = _haspermto_re.search(arg)
    if not match:
        raise TemplateSyntaxError('{!r} tag had invalid arguments: {!r}'.format(tag_name, arg))

    perm_type, entity_path, var_name = match.groups()

    perm_func = _PERMS_FUNCS.get(perm_type)
    if not perm_func:
        raise TemplateSyntaxError("{!r} invalid permission tag: {!r}".format(tag_name, perm_type))

    entity_var = TemplateLiteral(parser.compile_filter(entity_path), entity_path)

    return HasPermToNode(perm_func, entity_var, var_name)


class HasPermToNode(TemplateNode):
    def __init__(self, perm_func, entity_var, var_name):
        self.perm_func = perm_func
        self.entity_var = entity_var
        self.var_name = var_name

    def __repr__(self):
        return "<HasPermTo node>"

    def render(self, context):
        var  = self.entity_var.eval(context)  # Can raise template.VariableDoesNotExist...
        user = context['user']
        context[self.var_name] = self.perm_func(var, user)

        return ''

# TAG : "has_perm_to [end]------------------------------------------------------


@register.simple_tag(takes_context=True)
def creme_media_url(context, url):
    return get_creme_media_url(context.get('THEME_NAME') or settings.THEMES[0][0], url)


@register.tag(name='include_creme_media')
def do_include_creme_media(parser, token):
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError as e:
        raise TemplateSyntaxError('{!r} tag requires arguments'.format(token.contents.split()[0])) from e

    return MediaNode(TemplateLiteral(parser.compile_filter(arg), arg))


class MediaNode(TemplateNode):
    def __init__(self, bundle_var):
        self.bundle_var = bundle_var

    def render(self, context):
        bundle = self.bundle_var.eval(context)

        return _render_include_media(context['THEME_NAME'] + bundle, variation={})


# TODO: creme_backends module ? (wait for list-view rework to see if it's still useful)
@register.simple_tag
def get_export_backends():
    return json_dump([[backend.id, str(backend.verbose_name)]
                        for backend in export_backend_registry.backends
                     ]
                    )


@register.simple_tag
def get_import_backends():
    return json_dump([[backend.id] for backend in import_backend_registry.backends])


@register.simple_tag(name='hg_info')
def get_hg_info():
    from ..utils.version import get_hg_info

    return get_hg_info


@register.simple_tag(name='scm_info')
def get_scm_info():
    from ..utils import version

    scm = settings.SCM

    if scm == 'git':
        return version.get_git_info

    if scm == 'hg':
        return version.get_hg_info

    return None


@register.tag(name='blockjsondata')
def do_jsondata(parser, token):
    """ Encode json of the block and render it in a <script> tag with attributes.

    {% blockjsondata arg1=foo.bar arg2='baz' %}
        {{data}}
    {% endblockjsondata %}
    """
    nodelist = parser.parse(('endblockjsondata',))
    parser.delete_first_token()
    kwargs = token_kwargs(token.split_contents()[1:], parser)
    return JsonScriptNode(nodelist, kwargs)

class JsonScriptNode(TemplateNode):
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        output = self.nodelist.render(context)
        kwargs = self.kwargs

        if kwargs.pop("type", None) is not None:
            logger.warning('jsondatablock tag do not accept custom "type" attribute')

        attrs = ''.join(' {}="{}"'.format(k, escape(force_text(v.resolve(context)))) for k, v in kwargs.items())

        return mark_safe('<script type="application/json"{}><!-- {} --></script>'.format(attrs, escapejson(output)))
