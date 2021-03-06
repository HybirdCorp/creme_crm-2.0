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

from datetime import timedelta
import warnings

from django.conf import settings
from django.db.models import (Model, PositiveIntegerField, CharField, TextField,
        DateTimeField, ForeignKey, PROTECT)
from django.db.transaction import atomic
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# from creme.creme_core.core.function_field import FunctionField
from creme.creme_core.models import CremeEntity
# from creme.creme_core.templatetags.creme_date import timedelta_pprint

from .criticity import Criticity
from .priority import Priority
from .status import Status, OPEN_PK, CLOSED_PK


# class _ResolvingDurationField(FunctionField):
#     name         = 'get_resolving_duration'
#     verbose_name = _('Resolving duration')


class TicketNumber(Model):
    """This class is used to generate the value of Ticket.number.
    Only the ID/PK is useful, with its auto-increment feature:
        - the ID will be max ID + 1.
        - the max ID is kept even if the related Ticket is deleted.
    """
    class Meta:
        app_label = 'tickets'

    def __repr__(self):
        return 'TicketNumber(id={})'.format(self.id)


class TicketMixin(CremeEntity):
    title        = CharField(_('Title'), max_length=100, blank=True, null=False)
    description  = TextField(_('Description'))
    status       = ForeignKey(Status, verbose_name=_('Status'), on_delete=PROTECT).set_tags(clonable=False)
    priority     = ForeignKey(Priority, verbose_name=_('Priority'), on_delete=PROTECT)
    criticity    = ForeignKey(Criticity, verbose_name=_('Criticity'), on_delete=PROTECT)
    solution     = TextField(_('Solution'), blank=True, null=False)

    class Meta:
        app_label = 'tickets'
        abstract = True

    def __str__(self):
        return self.title


class AbstractTicket(TicketMixin):
    number       = PositiveIntegerField(_('Number'), unique=True, editable=False)\
                                       .set_tags(clonable=False)
    closing_date = DateTimeField(_('Closing date'), blank=True, null=True,
                                 editable=False,
                                ).set_tags(clonable=False)

    # function_fields = CremeEntity.function_fields.new(_ResolvingDurationField())

    creation_label = _('Create a ticket')
    save_label     = _('Save the ticket')

    class Meta:
        abstract = True
        manager_inheritance_from_future = True
        app_label = 'tickets'
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ('title',)

    def __init__(self, *args, **kwargs):
        # super(AbstractTicket, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.old_status_id = self.status_id

    def __str__(self):
        return '#{} - {}'.format(self.number, self.title)

    def get_absolute_url(self):
        return reverse('tickets__view_ticket', args=(self.id,))

    @staticmethod
    def get_create_absolute_url():
        return reverse('tickets__create_ticket')

    def get_edit_absolute_url(self):
        return reverse('tickets__edit_ticket', args=(self.id,))

    @staticmethod
    def get_lv_absolute_url():
        return reverse('tickets__list_tickets')

    def get_html_attrs(self, context):
        # attrs = super(AbstractTicket, self).get_html_attrs(context)
        attrs = super().get_html_attrs(context)

        if self.status_id == OPEN_PK and \
           (context['today'] - self.created) > timedelta(days=settings.TICKETS_COLOR_DELAY):
            attrs['data-color'] = 'tickets-important'

        return attrs

    def get_resolving_duration(self):
        warnings.warn('tickets.models.AbstractTicket.get_resolving_duration() is deprecated ; '
                      'use tickets.function_fields.ResolvingDurationField instead.',
                      DeprecationWarning
                     )

        from creme.creme_core.templatetags.creme_date import timedelta_pprint

        if self.status_id == CLOSED_PK:
            closing_date = self.closing_date

            return timedelta_pprint(closing_date - self.created) if closing_date else '?'

        return ''

    @atomic
    def save(self, *args, **kwargs):
        if self.pk:
            if (self.status_id == CLOSED_PK) and (self.old_status_id != CLOSED_PK):
                self.closing_date = now()
        else:  # Creation
            self.status_id = self.status_id or OPEN_PK

            # Number management
            number_id = TicketNumber.objects.create().id
            self.number = number_id
            TicketNumber.objects.filter(id__lt=number_id).delete()

        # super(AbstractTicket, self).save(*args, **kwargs)
        super().save(*args, **kwargs)


class Ticket(AbstractTicket):
    class Meta(AbstractTicket.Meta):
        swappable = 'TICKETS_TICKET_MODEL'


class AbstractTicketTemplate(TicketMixin):
    """Used by 'recurrents' app if it is installed"""
    creation_label = _('Create a ticket template')
    save_label     = _('Save the ticket template')

    class Meta:
        abstract = True
        manager_inheritance_from_future = True
        app_label = 'tickets'
        verbose_name = _('Ticket template')
        verbose_name_plural = _('Ticket templates')
        ordering = ('title',)

    def get_absolute_url(self):
        return reverse('tickets__view_template', args=(self.id,))

    @staticmethod
    def get_clone_absolute_url():
        return ''

    def get_edit_absolute_url(self):
        return reverse('tickets__edit_template', args=(self.id,))

    def get_delete_absolute_url(self):
        # Means that TicketTemplates can not be deleted directly
        # (because they are closely linked to their RecurrentGenerator)
        return ''

    @staticmethod
    def get_lv_absolute_url():
        return reverse('tickets__list_templates')

    def create_entity(self):
        """This method is used by the generation job of the 'recurrents' app"""
        from .. import get_ticket_model

        now_value = now()

        return get_ticket_model().objects\
                                 .create(user=self.user,
                                         title='{} {}'.format(
                                                    self.title,
                                                    date_format(now_value.date(), 'DATE_FORMAT'),
                                                ),  # TODO: use localtime() ?
                                         description=self.description,
                                         status_id=self.status_id,
                                         priority_id=self.priority_id,
                                         criticity_id=self.criticity_id,
                                         solution=self.solution,
                                         closing_date=(now_value if self.status_id == CLOSED_PK else None),
                                        )


class TicketTemplate(AbstractTicketTemplate):
    class Meta(AbstractTicketTemplate.Meta):
        swappable = 'TICKETS_TEMPLATE_MODEL'
