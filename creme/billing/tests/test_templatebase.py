# -*- coding: utf-8 -*-

try:
    from datetime import date, timedelta
    from functools import partial

    from django.contrib.contenttypes.models import ContentType
    from django.utils.translation import ugettext as _

    from creme.creme_core.core.function_field import function_field_registry
    from creme.creme_core.models import Relation

    from creme.persons.tests.base import skipIfCustomOrganisation

    from ..models import (InvoiceStatus, QuoteStatus, SalesOrderStatus,
            AdditionalInformation, PaymentTerms)
    from ..constants import REL_SUB_BILL_ISSUED, REL_SUB_BILL_RECEIVED
    from .base import (_BillingTestCase, skipIfCustomTemplateBase,
            skipIfCustomInvoice, skipIfCustomQuote, skipIfCustomSalesOrder,
            Organisation, TemplateBase, Invoice, Quote, SalesOrder)
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


@skipIfCustomOrganisation
@skipIfCustomTemplateBase
class TemplateBaseTestCase(_BillingTestCase):
    def setUp(self):
        self.login()

        create_orga = partial(Organisation.objects.create, user=self.user)
        self.source = create_orga(name='Source')
        self.target = create_orga(name='Target')

    def _create_templatebase(self, model, status_id, comment=''):
        user = self.user
        tpl = TemplateBase.objects.create(user=user,
                                          ct=ContentType.objects.get_for_model(model),
                                          status_id=status_id,
                                          comment=comment,
                                         )

        create_rel = partial(Relation.objects.create, user=user, subject_entity=tpl)
        create_rel(type_id=REL_SUB_BILL_ISSUED,   object_entity=self.source)
        create_rel(type_id=REL_SUB_BILL_RECEIVED, object_entity=self.target)

        return tpl

    def test_detailview(self):
        invoice_status1 = self.get_object_or_fail(InvoiceStatus, pk=3)
        tpl = self._create_templatebase(Invoice, invoice_status1.id)
        response = self.assertGET200(tpl.get_absolute_url())
        self.assertTemplateUsed(response, 'billing/view_template.html')

    def test_status01(self):
        invoice_status1 = self.get_object_or_fail(InvoiceStatus, pk=3)
        tpl = self._create_templatebase(Invoice, invoice_status1.id)

        with self.assertNumQueries(1):
            status_str = tpl.verbose_status

        self.assertEqual(str(invoice_status1), status_str)

        # Cache -------------------------
        with self.assertNumQueries(0):
            status_str = tpl.verbose_status

        self.assertEqual(str(invoice_status1), status_str)

        # Change status -------------------------
        invoice_status2 = self.get_object_or_fail(InvoiceStatus, pk=2)
        tpl.status_id = invoice_status2.id

        with self.assertNumQueries(1):
            status_str = tpl.verbose_status

        self.assertEqual(str(invoice_status2), status_str)

        # Invalid ID -------------------------
        tpl.status_id = invalid_id = 1024
        self.assertFalse(InvoiceStatus.objects.filter(id=invalid_id).exists())

        with self.assertNumQueries(1):
            status_str = tpl.verbose_status

        self.assertEqual('', status_str)

    def test_status02(self):
        "Other CT"
        quote_status = self.get_object_or_fail(QuoteStatus, pk=3)
        tpl = self._create_templatebase(Quote, quote_status.id)

        self.assertEqual(str(quote_status), tpl.verbose_status)

    def test_status_function_field(self):
        invoice_status = self.get_object_or_fail(InvoiceStatus, pk=3)
        tpl = self._create_templatebase(Invoice, invoice_status.id)

        with self.assertNoException():
            # funf = tpl.function_fields.get('get_verbose_status')
            funf = function_field_registry.get(TemplateBase, 'get_verbose_status')

        self.assertIsNotNone(funf)

        with self.assertNumQueries(1):
            status_str = funf(tpl, self.user).for_html()

        self.assertEqual(str(invoice_status), status_str)

        with self.assertNumQueries(0):
            funf(tpl, self.user).for_html()

    @skipIfCustomInvoice
    def test_create_invoice01(self):
        invoice_status = self.get_object_or_fail(InvoiceStatus, pk=3)
        comment = '*Insert a comment here*'
        tpl = self._create_templatebase(Invoice, invoice_status.id, comment)

        tpl.additional_info = AdditionalInformation.objects.all()[0]
        tpl.payment_terms = PaymentTerms.objects.all()[0]
        tpl.save()

        with self.assertNoException():
            invoice = tpl.create_entity()

        self.assertIsInstance(invoice, Invoice)
        self.assertEqual(comment, invoice.comment)
        self.assertEqual(invoice_status, invoice.status)
        self.assertEqual(tpl.additional_info, invoice.additional_info)
        self.assertEqual(tpl.payment_terms,   invoice.payment_terms)
        self.assertEqual(self.source, invoice.get_source().get_real_entity())
        self.assertEqual(self.target, invoice.get_target().get_real_entity())

        self.assertIsNotNone(invoice.number)
        self.assertEqual(date.today(), invoice.issuing_date)
        self.assertEqual(invoice.issuing_date + timedelta(days=30), invoice.expiration_date)

    @skipIfCustomInvoice
    def test_create_invoice02(self):
        "Bad status id"
        pk = 12
        self.assertFalse(InvoiceStatus.objects.filter(pk=pk))

        tpl = self._create_templatebase(Invoice, pk)

        with self.assertNoException():
            invoice = tpl.create_entity()

        self.assertEqual(1, invoice.status_id)

    @skipIfCustomQuote
    def test_create_quote01(self):
        quote_status = self.get_object_or_fail(QuoteStatus, pk=2)
        comment = '*Insert an nice comment here*'
        tpl = self._create_templatebase(Quote, quote_status.id, comment)

        with self.assertNoException():
            quote = tpl.create_entity()

        self.assertIsInstance(quote, Quote)
        self.assertEqual(comment, quote.comment)
        self.assertEqual(quote_status, quote.status)

    @skipIfCustomQuote
    def test_create_quote02(self):
        "Bad status id"
        pk = 8
        self.assertFalse(QuoteStatus.objects.filter(pk=pk))

        tpl = self._create_templatebase(Quote, pk)

        with self.assertNoException():
            quote = tpl.create_entity()

        status = quote.status
        self.assertIsNotNone(status)
        self.assertEqual(pk,    status.id)
        self.assertEqual(_(u'N/A'), status.name)

    @skipIfCustomSalesOrder
    def test_create_order01(self):
        order_status = self.get_object_or_fail(SalesOrderStatus, pk=4)
        tpl = self._create_templatebase(SalesOrder, order_status.id)

        with self.assertNoException():
            order = tpl.create_entity()

        self.assertIsInstance(order, SalesOrder)
        self.assertEqual(order_status, order.status)

    @skipIfCustomSalesOrder
    def test_create_order02(self):
        "Bad status id"
        pk = 8
        self.assertFalse(SalesOrder.objects.filter(pk=pk))

        tpl = self._create_templatebase(SalesOrder, pk)

        with self.assertNoException():
            order = tpl.create_entity()

        self.assertEqual(1, order.status.id)

    # TODO: test form
