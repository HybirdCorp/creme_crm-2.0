# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2017  Hybird
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

import logging, warnings

from django.utils.html import escape
from django.utils.safestring import mark_safe

from ..utils.media import get_creme_media_url


logger = logging.getLogger(__name__)


# TODO: Creme1.8 these info will be retrieved from theme data
_SVG_ICONS = {
    'chantilly': {
        'goto': {
            'view_box': "0 0 18 18",
            'path': "M9 3L7.94 4.06l4.19 4.19H3v1.5h9.13l-4.19 4.19L9 15l6-6z"
        },
        'reorder': {
            'view_box': "0 0 24 24",
            'path': "M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"
        },
        'reload': {
            'view_box': "0 0 18 18",
            'path': "M9 13.5c-2.49 0-4.5-2.01-4.5-4.5S6.51 4.5 9 4.5c1.24 0 2.36.52 3.17 1.33L10 8h5V3l-1.76 1.76C12.15 3.68 10.66 3 9 3 5.69 3 3.01 5.69 3.01 9S5.69 15 9 15c2.97 0 5.43-2.16 5.9-5h-1.52c-.46 2-2.24 3.5-4.38 3.5z"
        },
    },
    'icecream': {
        'goto':    {
            'view_box': '0 0 18 18',
            'path': 'M9 3L7.94 4.06l4.19 4.19H3v1.5h9.13l-4.19 4.19L9 15l6-6z',
        },
        'reorder': {
            'view_box': '0 0 24 24',
            'path': 'M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z',
        },
        'reload': {
            'view_box': '0 0 18 18',
            'path': 'M9 13.5c-2.49 0-4.5-2.01-4.5-4.5S6.51 4.5 9 4.5c1.24 0 2.36.52 3.17 1.33L10 8h5V3l-1.76 1.76C12.15 3.68 10.66 3 9 3 5.69 3 3.01 5.69 3.01 9S5.69 15 9 15c2.97 0 5.43-2.16 5.9-5h-1.52c-.46 2-2.24 3.5-4.38 3.5z',
        },
    },
}

# TODO: Creme1.8 these info will be retrieved from theme data
_ICON_SIZES_MAP = {
    'chantilly': {
        # Fall-backs (should be avoided)
        'big':    64,
        'high':   48,
        'medium': 32,
        'small':  22,
        'tiny':   16,

        # Semantic sizes (use these ones)
        # Brick sizes
        'brick-header':        48,
        'brick-header-action': 22,

        'brick-loading':       22,

        'brick-action':       22,
        'brick-table-action': 22,
        'brick-tile-action':  22,
        'brick-menu-action':  22,

        'brick-table': 22,
        'brick-list':  22,

        'brick-hat-bar':        64,
        'brick-hat-bar-button': 64,

        'brick-hat-card':         48,
        'brick-hat-card-intro':   22,
        'brick-hat-card-summary': 22,
        'brick-hat-card-button':  32,

        # Buttons
        'global-button':   32,
        'instance-button': 32,
    },
    'icecream': {
        # Fall-backs (should be avoided)
        'big':    48,
        'high':   32,
        'medium': 22,
        'small':  16,
        'tiny':   12,

        # Semantic sizes (use these ones)
        # Brick sizes
        'brick-header':           16,
        'brick-header-action':    12,  # TODO: 10 ?

        'brick-loading':          16,

        'brick-action':           16,
        'brick-table-action':     16,
        'brick-tile-action':      16,
        'brick-menu-action':      16,

        'brick-table':            16,
        'brick-list':             16,

        'brick-hat-bar':          48,  # TODO: 50 ?
        'brick-hat-bar-button':   48,  # TODO: 50 ?

        'brick-hat-card':         22,
        'brick-hat-card-intro':   16,
        'brick-hat-card-summary': 16,
        'brick-hat-card-button':  16,

        # Buttons
        'global-button':          16,
        'instance-button':        16,
    },
}


class BaseIcon(object):
    def __init__(self, size, label='', css_class=''):
        self.size = size

        self.label = label
        self.css_class = css_class

    def render(self, css_class=''):
        raise NotImplementedError


class Icon(BaseIcon):
    def __init__(self, url, *args, **kwargs):
        super(Icon, self).__init__(*args, **kwargs)
        self.url = url

    def render(self, css_class=''):
        final_css_class = self.css_class + css_class

        return mark_safe(u'<img src="{url}" {attrs} title="{label}" alt="{label}" width="{size}dpx"/>'.format(
                size=self.size,
                label=escape(self.label),
                attrs=u' class="{}"'.format(final_css_class) if final_css_class else '',
                url=self.url,
        ))


class SVGIcon(BaseIcon):
    def __init__(self, view_box, svg_path, *args, **kwargs):
        super(SVGIcon, self).__init__(*args, **kwargs)
        self.view_box = view_box
        self.svg_path = svg_path

    def render(self, css_class=''):
        final_css_class = self.css_class + css_class

        return mark_safe('<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {attrs} title="{label}" alt="{label}" height="{size}px" width="{size}px">'
                            '<path d="{path}"></path>'
                         '</svg>'.format(
                size=self.size,
                label=escape(self.label),
                attrs=u' class="{}"'.format(final_css_class) if final_css_class else '',
                box=self.view_box,
                path=self.svg_path,
        ))


def get_icon_size_px(theme, size='medium'):
    return _ICON_SIZES_MAP[theme][size]


def get_icon_by_name(name, theme, size_px, label='', css_class=''):
    try:
        svg_info = _SVG_ICONS[theme][name]
    except KeyError:
        pass
    else:
        return SVGIcon(view_box=svg_info['view_box'], svg_path=svg_info['path'],
                       size=size_px, label=label, css_class=css_class,
                      )

    def _get_image_url():
        try:
            return get_creme_media_url(theme, 'images/%s_%s.png' % (name, size_px))
        except KeyError:
            pass

        try:
            return get_creme_media_url(theme, 'images/%s.png' % name)
        except KeyError:
            pass

        try:
            return get_creme_media_url(theme, 'images/%s_%s.gif' % (name, size_px))
        except KeyError:
            pass

        try:
            return get_creme_media_url(theme, 'images/%s.gif' % name)
        except KeyError:
            pass

        logger.warn('Missing image: %s (theme="%s", size=%s)', name, theme, size_px)

        return ''

    return Icon(url=_get_image_url(), size=size_px, label=label, css_class=css_class)


class IconRegistry(object):
    def __init__(self):
        self._icons = {}
        self._icons_4_objects = {}

    def register(self, model, path):
        """eg: icon_registry.register(Ticket, 'images/ticket_%(size)s.png')"""
        self._icons[model] = path

    def register_4_instance(self, model, info_function):
        """Setup the registry in order to retrieve an Icon corresponding to an instance of a model.
        Ie: instances of a same type can have different Icons.

        @param model: Class inheriting django.db.models.Model.
        @param info_function: A callable which
                                - takes 1 argument 'instance'.
                                - returns a tuple (icon_base_name, label).

        Note: If yours icons names have the pattern 'images/foobar_%(size)s.png', so icon_base_name == 'foobar'.
              Notice that it means there is currently a limitation on the image name/format.
        """
        self._icons_4_objects[model] = info_function

    def get(self, model, size):
        warnings.warn('The method creme_core.gui.icons.IconRegistry.get() is deprecated ; '
                      'use IconRegistry.get_4_model() instead.',
                      DeprecationWarning
                     )

        path = self._icons.get(model)
        return path and (path % {'size': size})

    def get_4_model(self, model, theme, size_px):
        url = ''
        path_fmt = self._icons.get(model)

        if path_fmt:
            path = path_fmt % {'size': size_px}

            try:
                url = get_creme_media_url(theme, path)
            except KeyError:
                logger.warn('Missing image: %s', path)

        return Icon(url=url, size=size_px, label=model._meta.verbose_name)

    def get_4_instance(self, instance, theme, size_px):
        url = ''
        path_fmt = label = ''
        model = instance.__class__
        icon_info_function = self._icons_4_objects.get(model)

        if icon_info_function:
            info = icon_info_function(instance)
            if info:
                # TODO: improve (with the future creme 1.8 asset managers) in order
                #       to manage other formats (see SVGIcon etc...)
                path_fmt = 'images/' + info[0] + '_%(size)s.png'
                label = info[1]

        if not path_fmt:
            path_fmt = self._icons.get(model)

        if path_fmt:
            path = path_fmt % {'size': size_px}

            try:
                url = get_creme_media_url(theme, path)
            except KeyError:
                logger.warn('Missing image: %s', path)

        return Icon(url=url, size=size_px,
                    label=label or instance._meta.verbose_name,
                   )


icon_registry = IconRegistry()