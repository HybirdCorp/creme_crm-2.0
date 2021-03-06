# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from creme.creme_core.conf.urls import Swappable, swap_manager

from creme.opportunities import opportunity_model_is_custom

from . import event_model_is_custom
from .views import event  # portal


urlpatterns = [
    # url(r'^$', portal.portal, name='events__portal'),

    url(r'^event/(?P<event_id>\d+)/contacts[/]?$', event.list_contacts, name='events__list_related_contacts'),
    url(r'^event/(?P<event_id>\d+)/link_contacts[/]?$',
        # event.link_contacts
        event.AddContactsToEvent.as_view(),
        name='events__link_contacts',
    ),

    url(r'^event/(?P<event_id>\d+)/contact/(?P<contact_id>\d+)/', include([
        url(r'^set_invitation_status[/]?$', event.set_invitation_status, name='events__set_invitation_status'),
        url(r'^set_presence_status[/]?$',   event.set_presence_status,   name='events__set_presence_status'),
    ])),
]

# if not event_model_is_custom():
#     urlpatterns += [
#         url(r'^events[/]?$',                       event.listview,   name='events__list_events'),
#         url(r'^event/add[/]?$',                    event.add,        name='events__create_event'),
#         url(r'^event/edit/(?P<event_id>\d+)[/]?$', event.edit,       name='events__edit_event'),
#         url(r'^event/(?P<event_id>\d+)[/]?$',      event.detailview, name='events__view_event'),
#     ]
urlpatterns += swap_manager.add_group(
    event_model_is_custom,
    Swappable(url(r'^events[/]?$',                       event.listview,                name='events__list_events')),
    Swappable(url(r'^event/add[/]?$',                    event.EventCreation.as_view(), name='events__create_event')),
    Swappable(url(r'^event/edit/(?P<event_id>\d+)[/]?$', event.EventEdition.as_view(),  name='events__edit_event'), check_args=Swappable.INT_ID),
    Swappable(url(r'^event/(?P<event_id>\d+)[/]?$',      event.EventDetail.as_view(),   name='events__view_event'), check_args=Swappable.INT_ID),
    app_name='events',
).kept_patterns()

# if not opportunity_model_is_custom():
#     urlpatterns += [
#         url(r'^event/(?P<event_id>\d+)/add_opportunity_with/(?P<contact_id>\d+)[/]?$',
#             event.add_opportunity,
#             name='events__create_related_opportunity',
#            ),
#     ]
urlpatterns += swap_manager.add_group(
    opportunity_model_is_custom,
    Swappable(url(r'^event/(?P<event_id>\d+)/add_opportunity_with/(?P<contact_id>\d+)[/]?$',
                  event.RelatedOpportunityCreation.as_view(),
                  name='events__create_related_opportunity',
                 ),
              check_args=(1, 2),
             ),
    app_name='events',
).kept_patterns()

