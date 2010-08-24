# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns


urlpatterns = patterns('billing.views',
    (r'^$', 'portal.portal'),

    (r'^odt/(?P<base_id>\d*)$', 'export.export_odt'),
    (r'^pdf/(?P<base_id>\d*)$', 'export.export_pdf'),

    (r'^templates$',                            'templatebase.listview'),
    (r'^template/edit/(?P<template_id>\d+)$',   'templatebase.edit'),
    (r'^template/(?P<template_id>\d+)$',        'templatebase.detailview'),
    (r'^template/delete/(?P<template_id>\d+)$', 'templatebase.delete'),

    (r'^sales_orders$',                       'sales_order.listview'),
    (r'^sales_order/add$',                    'sales_order.add'),
    (r'^sales_order/edit/(?P<order_id>\d+)$', 'sales_order.edit'),
    (r'^sales_order/(?P<order_id>\d+)$',      'sales_order.detailview'),

    (r'^quotes$',                       'quote.listview'),
    (r'^quote/add$',                    'quote.add'),
    (r'^quote/edit/(?P<quote_id>\d+)$', 'quote.edit'),
    (r'^quote/(?P<quote_id>\d+)$',      'quote.detailview'),
    

    (r'^credit_note$',                       'credit_note.listview'),
    (r'^credit_note/add$',                    'credit_note.add'),
    (r'^credit_note/edit/(?P<credit_note_id>\d+)$', 'credit_note.edit'),
    (r'^credit_note/(?P<credit_note_id>\d+)$',      'credit_note.detailview'),
    

    (r'^invoices$',                         'invoice.listview'),
    (r'^invoice/add$',                      'invoice.add'),
    (r'^invoice/edit/(?P<invoice_id>\d+)$', 'invoice.edit'),
    (r'^invoice/(?P<invoice_id>\d+)$',      'invoice.detailview'),

    (r'^(?P<document_id>\d+)/convert/$', 'convert.convert'),

    (r'^(?P<document_id>\d+)/product_line/add$',            'line.add_product_line'),
    (r'^(?P<document_id>\d+)/product_line/add_on_the_fly$', 'line.add_product_line_on_the_fly'),
    (r'^(?P<document_id>\d+)/service_line/add$',            'line.add_service_line'),
    (r'^(?P<document_id>\d+)/service_line/add_on_the_fly$', 'line.add_service_line_on_the_fly'),
    (r'^line/(?P<line_id>\d+)/update$',                     'line.update'),
    (r'^line/delete$',                                      'line.delete'),
    (r'^productline/(?P<line_id>\d+)/edit$',                'line.edit_productline'),
    (r'^serviceline/(?P<line_id>\d+)/edit$',                'line.edit_serviceline'),
)

urlpatterns += patterns('creme_core.views',
    (r'^invoice/edit_js/$',                                'ajax.edit_js'),
    (r'^invoice/delete/(?P<object_id>\d+)$',               'generic.delete_entity'),
    (r'^invoice/delete_js/(?P<entities_ids>([\d]+[,])+)$', 'generic.delete_entities_js'),

    (r'^quote/edit_js/$',                                'ajax.edit_js'),
    (r'^quote/delete/(?P<object_id>\d+)$',               'generic.delete_entity'),
    (r'^quote/delete_js/(?P<entities_ids>([\d]+[,])+)$', 'generic.delete_entities_js'),

    (r'^sales_order/edit_js/$',                                'ajax.edit_js'),
    (r'^sales_order/delete/(?P<object_id>\d+)$',               'generic.delete_entity'),
    (r'^sales_order/delete_js/(?P<entities_ids>([\d]+[,])+)$', 'generic.delete_entities_js'),
)
