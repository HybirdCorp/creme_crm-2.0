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

from django.db.models import ForeignKey, PROTECT
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from .base import Base
from .templatebase import TemplateBase
from .other_models import SalesOrderStatus


class AbstractSalesOrder(Base):
    status = ForeignKey(SalesOrderStatus, verbose_name=_(u'Status of salesorder'), on_delete=PROTECT)

    creation_label = _(u'Create a salesorder')
    save_label     = _(u'Save the salesorder')

    search_score = 50

    class Meta(Base.Meta):
        abstract = True
        verbose_name = _(u'Salesorder')
        verbose_name_plural = _(u'Salesorders')

    def get_absolute_url(self):
        return reverse('billing__view_order', args=(self.id,))

    @staticmethod
    def get_create_absolute_url():
        return reverse('billing__create_order')

    def get_edit_absolute_url(self):
        return reverse('billing__edit_order', args=(self.id,))

    @staticmethod
    def get_lv_absolute_url():
        return reverse('billing__list_orders')

    def build(self, template):
        # Specific recurrent generation rules
        # TODO: factorise with Invoice.build()
        status_id = 1  # Default status (see populate.py)

        if isinstance(template, TemplateBase):
            tpl_status_id = template.status_id
            if SalesOrderStatus.objects.filter(pk=tpl_status_id).exists():
                status_id = tpl_status_id

        self.status_id = status_id

        # return super(AbstractSalesOrder, self).build(template)
        return super().build(template)


class SalesOrder(AbstractSalesOrder):
    class Meta(AbstractSalesOrder.Meta):
        swappable = 'BILLING_SALES_ORDER_MODEL'
