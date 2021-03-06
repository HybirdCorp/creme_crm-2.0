# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from creme.creme_core.conf.urls import Swappable, swap_manager

from . import activity_model_is_custom, constants
from .views import activity, bricks, calendar  # portal


calendar_patterns = [
    url(r'^user[/]?$',                      calendar.user_calendar,              name='activities__calendar'),
    url(r'^activities[/]?$',                calendar.get_users_activities,       name='activities__calendars_activities'),
    # url(r'^users_activities/(?P<calendar_ids>([\d]+){0,1}(,[\d]+)*)[/]?$', calendar.get_users_activities, name='activities__calendars_activities'),
    url(r'^activity/update[/]?$',           calendar.update_activity_date,       name='activities__set_activity_dates'),
    # url(r'^add[/]?$',                       calendar.add_user_calendar,    name='activities__create_calendar'),
    url(r'^add[/]?$',                       calendar.CalendarCreation.as_view(), name='activities__create_calendar'),
    # url(r'^(?P<calendar_id>\d+)/edit[/]?$', calendar.edit_user_calendar,   name='activities__edit_calendar'),
    url(r'^(?P<calendar_id>\d+)/edit[/]?$', calendar.CalendarEdition.as_view(),  name='activities__edit_calendar'),
    url(r'^delete[/]?$',                    calendar.delete_user_calendar,       name='activities__delete_calendar'),
    # url(r'^link/(?P<activity_id>\d+)[/]?$', calendar.link_user_calendar,   name='activities__link_calendar'),
    url(r'^link/(?P<activity_id>\d+)[/]?$', calendar.CalendarLinking.as_view(),  name='activities__link_calendar'),
]

urlpatterns = [
    # url(r'^$', portal.portal, name='activities__portal'),

    url(r'^activities/ical[/]?$', activity.download_ical, name='activities__dl_ical'),

    url(r'^type/(?P<type_id>[\w-]*)/json[/]?$', activity.get_types, name='activities__get_types'),

    # Bricks
    # url(r'^activity/(?P<activity_id>\d+)/participant/add[/]?$', bricks.add_participant,    name='activities__add_participants'),
    url(r'^activity/(?P<activity_id>\d+)/participant/add[/]?$', bricks.ParticipantsAdding.as_view(), name='activities__add_participants'),
    url(r'^activity/participant/delete[/]?$',                   bricks.delete_participant,           name='activities__remove_participant'),
    # url(r'^activity/(?P<activity_id>\d+)/subject/add[/]?$',     bricks.add_subject,        name='activities__add_subjects'),
    url(r'^activity/(?P<activity_id>\d+)/subject/add[/]?$',     bricks.SubjectsAdding.as_view(),     name='activities__add_subjects'),
    url(r'^linked_activity/unlink[/]?$',                        bricks.unlink_activity,              name='activities__unlink_activity'),

    url(r'^calendar/', include(calendar_patterns)),
]

# if not activity_model_is_custom():
#     urlpatterns += [
#         url(r'^activities[/]?$',  activity.listview,                                                name='activities__list_activities'),
#         url(r'^phone_calls[/]?$', activity.listview, {'type_id': constants.ACTIVITYTYPE_PHONECALL}, name='activities__list_phone_calls'),
#         url(r'^meetings[/]?$',    activity.listview, {'type_id': constants.ACTIVITYTYPE_MEETING},   name='activities__list_meetings'),
#
#         url(r'^activity/add[/]?$',                            activity.add,                 name='activities__create_activity'),
#         url(r'^activity/add/(?P<act_type>\w+)[/]?$',          activity.add,                 name='activities__create_activity'),
#         url(r'^activity/add_indispo[/]?$',                    activity.add_indisponibility, name='activities__create_indispo'),
#         url(r'^activity/add_popup[/]?$',                      activity.add_popup,           name='activities__create_activity_popup'),
#         url(r'^activity/add_related/(?P<entity_id>\d+)[/]?$', activity.add_related,         name='activities__create_related_activity'),
#         url(r'^activity/edit/(?P<activity_id>\d+)[/]?$',      activity.edit,                name='activities__edit_activity'),
#         url(r'^activity/(?P<activity_id>\d+)[/]?$',           activity.detailview,          name='activities__view_activity'),
#         url(r'^activity/(?P<activity_id>\d+)/popup[/]?$',     activity.popupview,           name='activities__view_activity_popup'),
#     ]

urlpatterns += swap_manager.add_group(
    activity_model_is_custom,
    Swappable(url(r'^activities[/]?$',  activity.listview,                                                name='activities__list_activities')),
    Swappable(url(r'^phone_calls[/]?$', activity.listview, {'type_id': constants.ACTIVITYTYPE_PHONECALL}, name='activities__list_phone_calls')),
    Swappable(url(r'^meetings[/]?$',    activity.listview, {'type_id': constants.ACTIVITYTYPE_MEETING},   name='activities__list_meetings')),

    Swappable(url(r'^activity/add[/]?$',                            activity.ActivityCreation.as_view(),        name='activities__create_activity')),
    Swappable(url(r'^activity/add/(?P<act_type>\w+)[/]?$',          activity.ActivityCreation.as_view(),        name='activities__create_activity'),         check_args=('idxxx',)),
    Swappable(url(r'^activity/add_indispo[/]?$',                    activity.UnavailabilityCreation.as_view(),  name='activities__create_indispo')),
    Swappable(url(r'^activity/add_popup[/]?$',                      activity.ActivityCreationPopup.as_view(),   name='activities__create_activity_popup')),
    Swappable(url(r'^activity/add_related/(?P<entity_id>\d+)[/]?$', activity.RelatedActivityCreation.as_view(), name='activities__create_related_activity'), check_args=Swappable.INT_ID),
    Swappable(url(r'^activity/edit/(?P<activity_id>\d+)[/]?$',      activity.ActivityEdition.as_view(),         name='activities__edit_activity'),           check_args=Swappable.INT_ID),
    Swappable(url(r'^activity/(?P<activity_id>\d+)[/]?$',           activity.ActivityDetail.as_view(),          name='activities__view_activity'),           check_args=Swappable.INT_ID),
    Swappable(url(r'^activity/(?P<activity_id>\d+)/popup[/]?$',     activity.ActivityPopup.as_view(),           name='activities__view_activity_popup'),     check_args=Swappable.INT_ID),
    app_name='activities',
).kept_patterns()
