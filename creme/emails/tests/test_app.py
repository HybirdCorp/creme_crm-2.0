# -*- coding: utf-8 -*-

try:
    # from django.urls import reverse
    from django.utils.translation import ugettext as _

    from creme.creme_core.models import SettingValue, FieldsConfig

    from creme.persons.tests.base import skipIfCustomContact

    from ..constants import (REL_SUB_MAIL_RECEIVED, REL_SUB_MAIL_SENDED,
            REL_SUB_RELATED_TO, SETTING_EMAILCAMPAIGN_SENDER)
    from .base import _EmailsTestCase, Contact, Organisation, EntityEmail
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


class EmailsTestCase(_EmailsTestCase):
    def test_populate(self):
        self.get_relationtype_or_fail(REL_SUB_MAIL_RECEIVED, [EntityEmail], [Organisation, Contact])
        self.get_relationtype_or_fail(REL_SUB_MAIL_SENDED,   [EntityEmail], [Organisation, Contact])
        self.get_relationtype_or_fail(REL_SUB_RELATED_TO,    [EntityEmail])

        self.assertEqual(1, SettingValue.objects.filter(key_id=SETTING_EMAILCAMPAIGN_SENDER).count())

    # def test_portal(self):
    #     self.login()
    #     self.assertGET200(reverse('emails__portal'))

    @skipIfCustomContact
    def test_fieldconfigs_warning(self):
        "If Contact/Organisation.email is hidden => warning"
        self.login()

        fconf = FieldsConfig.create(Contact)
        self.assertEqual([], fconf.errors_on_hidden)

        fconf.descriptions = [('email', {FieldsConfig.HIDDEN: True})]
        fconf.save()
        fconf = self.refresh(fconf)
        self.assertEqual([_(u'Warning: the app «{app}» need the field «{field}».').format(
                                app=_(u'Emails'),
                                field=_(u'Email address'),
                            ),
                         ],
                         fconf.errors_on_hidden
                        )
