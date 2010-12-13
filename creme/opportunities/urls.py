# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns


urlpatterns = patterns('opportunities.views',
    (r'^$', 'portal.portal'),

    (r'^opportunities$',                            'opportunity.listview'),
    (r'^opportunity/add$',                          'opportunity.add'),
    (r'^opportunity/add_to_orga/(?P<orga_id>\d+)$', 'opportunity.add_to_orga'),
    (r'^opportunity/edit/(?P<opp_id>\d+)$',         'opportunity.edit'),
    (r'^opportunity/(?P<opp_id>\d+)$',              'opportunity.detailview'),

    (r'^opportunity/generate_new_doc/(?P<opp_id>\d+)/(?P<ct_id>\d+)$', 'opportunity.generate_new_doc'),

    (r'^opportunity/(?P<opp_id>\d+)/linked/quote/(?P<quote_id>\d+)/set_current/$', 'links.set_current_quote'),
)

urlpatterns += patterns('creme_core.views.generic',
    (r'^opportunity/delete/(?P<object_id>\d+)$',               'delete_entity'),
    #(r'^opportunity/delete_js/(?P<entities_ids>([\d]+[,])+)$', 'delete_entities_js'), #Commented 6 december 2010
)
