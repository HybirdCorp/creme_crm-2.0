# -*- coding: utf-8 -*-

try:
    from django.utils.translation import ugettext as _
    from django.test import override_settings

    from django.urls import reverse

    from creme.creme_core.tests.base import CremeTestCase
    from creme.creme_core.tests.views.base import BrickTestCaseMixin
    from creme.creme_core.models import SettingValue

    from .. import setting_keys, constants, bricks
    from ..utils import is_user_sync_calendars, is_user_sync_contacts
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


class GlobalSettingsTestCase(CremeTestCase, BrickTestCaseMixin):
    def test_editview(self):
        self.login()
        url = reverse('activesync__edit_mobile_config')
        self.assertGET200(url)

        sv_url    = self.get_object_or_fail(SettingValue, key_id=constants.MAPI_SERVER_URL)
        sv_domain = self.get_object_or_fail(SettingValue, key_id=constants.MAPI_DOMAIN)
        sv_ssl    = self.get_object_or_fail(SettingValue, key_id=constants.MAPI_SERVER_SSL)

        server_url = 'http://cremecrm.com/as'
        server_domain = 'creme'
        response = self.client.post(url, data={'url':    server_url,
                                               'domain': server_domain,
                                               'ssl':    'on',
                                              }
                                   )
        self.assertNoFormError(response)

        with self.assertNoException():
            sv_url    = self.refresh(sv_url)
            sv_domain = self.refresh(sv_domain)
            sv_ssl    = self.refresh(sv_ssl)

        self.assertEqual(server_url,    sv_url.value)
        self.assertEqual(server_domain, sv_domain.value)
        self.assertIs(sv_ssl.value, True)

        response = self.assertGET200(url)

        with self.assertNoException():
            form = response.context['form']

        self.assertEqual({'url': server_url, 'domain': server_domain, 'ssl': True},
                         form.initial
                        )

    def test_config_page(self):
        self.login()
        response = self.assertGET200(reverse('creme_config__app_portal', args=('activesync',)))
        self.get_brick_node(self.get_html_tree(response.content), bricks.MobileSyncConfigBrick.id_)


class UserSettingsTestCase(CremeTestCase):
    URL = reverse('activesync__user_settings')

    def _assertNoSValue(self, skeys, user):
        user_settings = user.settings

        for skey in skeys:
            try:
                user_settings[skey]
            except KeyError:
                pass
            else:
                self.fail('The key %s exists' % skey.id)

    def test_is_user_sync_calendars(self):
        user = self.login()

        with self.assertRaises(KeyError):
            user.settings[setting_keys.user_msync_activities_key]

        self.assertIs(False, is_user_sync_calendars(user))

        # --------------
        with user.settings as settings:
            settings[setting_keys.user_msync_activities_key] = True

        self.assertIs(True, is_user_sync_calendars(self.refresh(user)))

    def test_is_user_sync_contacts(self):
        user = self.login()

        with self.assertRaises(KeyError):
            user.settings[setting_keys.user_msync_contacts_key]

        self.assertIs(False, is_user_sync_contacts(user))

        # --------------
        with user.settings as settings:
            settings[setting_keys.user_msync_contacts_key] = True

        self.assertIs(True, is_user_sync_contacts(self.refresh(user)))

    def test_view(self):
        user = self.login()
        other_user = self.other_user

        skeys = [setting_keys.user_msync_server_url_key,
                 setting_keys.user_msync_server_domain_key,
                 setting_keys.user_msync_server_ssl_key,
                 setting_keys.user_msync_server_login_key,
                 setting_keys.user_msync_server_pwd_key,
                 setting_keys.user_msync_activities_key,
                 setting_keys.user_msync_contacts_key,
                ]

        url = self.URL
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields
            url_f    = fields['url']
            domain_f = fields['domain']
            ssl_f    = fields['ssl']
            login_f  = fields['login']
            pwd_f    = fields['password']
            sync_calendars_f = fields['sync_calendars']
            sync_contacts_f  = fields['sync_contacts']

        self.assertEqual('', url_f.initial)
        self.assertEqual('', domain_f.initial)
        self.assertEqual(0, ssl_f.initial)
        self.assertEqual('', login_f.initial)
        self.assertIsNone(pwd_f.initial)
        self.assertEqual(0, sync_calendars_f.initial)
        self.assertEqual(0, sync_contacts_f.initial)

        self._assertNoSValue(skeys, user)
        self._assertNoSValue(skeys, other_user)

        server_url = 'http://cremecrm.com/as'
        server_domain = 'creme'
        login = 'fulbert'
        pwd = 'fulbert_pwd'
        response = self.client.post(url, data={'url':            server_url,
                                               'domain':         server_domain,
                                               'ssl':            '1',
                                               'login':          login,
                                               'password':       pwd,
                                               'sync_calendars': '1',
                                               'sync_contacts':  '0',
                                              }
                                   )
        self.assertNoFormError(response)
        self._assertNoSValue(skeys, self.refresh(other_user))

        get_settings = self.refresh(user).settings.get
        self.assertEqual(server_url,    get_settings(setting_keys.user_msync_server_url_key))
        self.assertEqual(server_domain, get_settings(setting_keys.user_msync_server_domain_key))
        self.assertEqual(login,         get_settings(setting_keys.user_msync_server_login_key))
        self.assertIs(True,  get_settings(setting_keys.user_msync_server_ssl_key))
        self.assertIs(True,  get_settings(setting_keys.user_msync_activities_key))
        self.assertIs(False, get_settings(setting_keys.user_msync_contacts_key))

        # Other values --------------------------------------------------------
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields
            url_f    = fields['url']
            domain_f = fields['domain']
            ssl_f    = fields['ssl']
            login_f  = fields['login']
            pwd_f    = fields['password']
            sync_calendars_f = fields['sync_calendars']
            sync_contacts_f  = fields['sync_contacts']

        self.assertEqual(server_url, url_f.initial)
        self.assertEqual(_(u"Let empty to get the default configuration (currently '%s').") % '',
                         url_f.help_text
                        )

        self.assertEqual(server_domain, domain_f.initial)
        self.assertEqual(_(u"Let empty to get the default configuration (currently '%s').") % '',
                         domain_f.help_text
                        )

        self.assertEqual(1, ssl_f.initial)
        self.assertEqual(_(u"Let 'Default' to get the default configuration (currently '%s').") % _('No'),
                         ssl_f.help_text
                        )

        self.assertEqual(login, login_f.initial)
        self.assertEqual(pwd,   pwd_f.initial)
        self.assertEqual(1,     sync_calendars_f.initial)
        self.assertEqual(0,     sync_contacts_f.initial)

        server_url = 'http://cremecrm.fr/as'
        server_domain = 'cremecrm'
        login = 'kirika'
        response = self.client.post(url, data={'url':            server_url,
                                               'domain':         server_domain,
                                               'ssl':            '0',
                                               'login':          login,
                                               'password':       'fulbert_pwd',
                                               'sync_calendars': '0',
                                               'sync_contacts':  '1',
                                              }
                                   )
        self.assertNoFormError(response)

        get_settings = self.refresh(user).settings.get
        self.assertEqual(server_url,    get_settings(setting_keys.user_msync_server_url_key))
        self.assertEqual(server_domain, get_settings(setting_keys.user_msync_server_domain_key))
        self.assertEqual(login,         get_settings(setting_keys.user_msync_server_login_key))
        self.assertFalse(get_settings(setting_keys.user_msync_server_ssl_key))
        self.assertFalse(get_settings(setting_keys.user_msync_activities_key))
        self.assertTrue(get_settings(setting_keys.user_msync_contacts_key))

        # Empty values --------------------------------------------------------
        response = self.client.post(url, data={'ssl':            '',
                                               'sync_calendars': '0',
                                               'sync_contacts':  '0',
                                              }
                                   )
        self.assertNoFormError(response)

        user = self.refresh(user)
        self._assertNoSValue([setting_keys.user_msync_server_url_key,
                              setting_keys.user_msync_server_domain_key,
                              setting_keys.user_msync_server_ssl_key,
                              setting_keys.user_msync_server_login_key,
                              setting_keys.user_msync_server_pwd_key,
                             ],
                             user
                            )

        get_settings = user.settings.get
        self.assertFalse(get_settings(setting_keys.user_msync_activities_key))
        self.assertFalse(get_settings(setting_keys.user_msync_contacts_key))

    def _aux_test_sync_view_error(self, url):
        self.login()

        self.client.post(self.URL,
                         data={'url':            url,
                               'ssl':            '1',
                               'login':          'fulbert',
                               'password':       'fulbert',
                               'sync_calendars': '1',
                               'sync_contacts':  '1',
                              },
                        )

        self.assertGET200(reverse('activesync__sync'))
        # TODO: test errors

    @override_settings(ACTIVE_SYNC_DEBUG=False)
    def test_sync_view_error01(self):
        self._aux_test_sync_view_error('http://toto.com')

    @override_settings(ACTIVE_SYNC_DEBUG=False)
    def test_sync_view_error02(self):
        self._aux_test_sync_view_error('http://invalid.com')

    @override_settings(ACTIVE_SYNC_DEBUG=True)
    def test_sync_view_error03(self):
        self._aux_test_sync_view_error('http://toto.com')

    @override_settings(ACTIVE_SYNC_DEBUG=True)
    def test_sync_view_error04(self):
        self._aux_test_sync_view_error('http://invalid.com')
