# -*- coding: utf-8 -*-

from django.conf.urls import url

from .views import actions, history, infopath, email, filesystem


urlpatterns = [
    # url(r'^waiting_actions[/]?$',          actions.portal,        name='crudity__actions'),
    url(r'^waiting_actions[/]?$',          actions.Portal.as_view(), name='crudity__actions'),
    url(r'^waiting_actions/refresh[/]?$',  actions.refresh,          name='crudity__refresh_actions'),
    url(r'^waiting_actions/delete[/]?$',   actions.delete,           name='crudity__delete_actions'),
    url(r'^waiting_actions/validate[/]?$', actions.validate,         name='crudity__validate_actions'),
    url(r'^waiting_actions/reload[/]?$',   actions.reload_bricks,    name='crudity__reload_actions_bricks'),

    # url(r'^history[/]?$',        history.history,        name='crudity__history'),
    url(r'^history[/]?$',        history.History.as_view(), name='crudity__history'),
    url(r'^history/reload[/]?$', history.reload_bricks,     name='crudity__reload_history_bricks'),

    # TODO: only one URL which handles all templates ?
    url(r'^infopath/create_form/(?P<subject>\w+)[/]?$',    infopath.create_form,             name='crudity__dl_infopath_form'),
    url(r'^download_email_template/(?P<subject>\w+)[/]?$', email.download_email_template,    name='crudity__dl_email_template'),
    url(r'^download_ini_template/(?P<subject>\w+)[/]?$',   filesystem.download_ini_template, name='crudity__dl_fs_ini_template'),
]
