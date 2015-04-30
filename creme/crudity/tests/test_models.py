# -*- coding: utf-8 -*-

try:
    from functools import partial

    from django.contrib.auth import get_user_model
    from django.contrib.contenttypes.models import ContentType
    from django.utils.timezone import now

    from creme.creme_core.models import CremeEntity
    from creme.creme_core.tests.fake_models import FakeContact as Contact

#    from creme.persons.models import Contact

    from ..models import WaitingAction
    from .base import CrudityTestCase
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class WaitingActionTestCase(CrudityTestCase):
    @classmethod
    def setUpClass(cls):
        CrudityTestCase.setUpClass()

        get_ct = ContentType.objects.get_for_model
        cls.ct_entity  = get_ct(CremeEntity)
        cls.ct_contact = get_ct(Contact)

        cls.User = get_user_model()
        cls._staff_user_ids_backup = list(cls.User.objects.filter(is_staff=True)
                                                          .values_list('id')
                                         )

    @classmethod
    def tearDownClass(cls):
        CrudityTestCase.tearDownClass()
        cls.User.objects.exclude(id__in=cls._staff_user_ids_backup).update(is_staff=False)

    def test_can_validate_or_delete01(self):
        "Sandbox for everyone"
        action = WaitingAction.objects.create(user=None, source="unknown",
                                              action="create", subject="",
                                              ct=self.ct_entity,
                                             )
        self.assertTrue(action.can_validate_or_delete(self.user)[0])
        self.assertTrue(action.can_validate_or_delete(self.other_user)[0])

    def test_can_validate_or_delete02(self):
        "Sandbox by user"
        self._set_sandbox_by_user()

        create_waction = partial(WaitingAction.objects.create, source="unknown",
                                 action="create", subject="", ct=self.ct_entity,
                                )
        action = create_waction(user=self.user)
        self.assertTrue(action.can_validate_or_delete(self.user)[0])
        self.assertFalse(action.can_validate_or_delete(self.other_user)[0])

        action2 = create_waction(user=self.other_user)
        self.assertTrue(action2.can_validate_or_delete(self.user)[0])
        self.assertTrue(action2.can_validate_or_delete(self.other_user)[0])

    def test_auto_assignation01(self):
        """If the sandbox was not by user, but now it is all WaitingAction has
        to be assigned to someone.
        """
        action = WaitingAction.objects.create(source="unknown", action="create",
                                              subject="", ct=self.ct_entity,
                                             )
        self.assertIsNone(action.user)

        self.assertTrue(self.User.objects.filter(is_superuser=True, is_staff=False))

        #Sandbox will be by user
        self._set_sandbox_by_user()
        self.assertFalse(WaitingAction.objects.filter(user=None))

        action = self.refresh(action)
        self.assertTrue(action.user.is_superuser)
        self.assertFalse(action.user.is_staff)

    def test_auto_assignation02(self):
        action = WaitingAction.objects.create(source="unknown", action="create",
                                              subject="", ct=self.ct_entity,
                                             )
        self.assertIsNone(action.user)

        self.User.objects.filter(is_superuser=True).update(is_staff=True)

        superuser = self.User.objects.create(username='Kirika2', is_superuser=True)

        self._set_sandbox_by_user()
        self.assertFalse(WaitingAction.objects.filter(user=None))
        self.assertEqual(superuser, self.refresh(action).user)

    def test_data_property01(self):
        action = WaitingAction(ct=self.ct_contact)
        expected_data = {u'first_name': u'Mario', u'last_name': u'Bros'}
        action.data = action.set_data(expected_data)
        action.save()

        self.assertEqual(expected_data, self.refresh(action).get_data())

    def test_data_property02(self):
        action = WaitingAction(ct=self.ct_contact)
        expected_data = {u'first_name': u'Mario', u'last_name': u'Bros',
                         u"friends": [u"Yoshi", u"Toad"], u"lives": 99,
                         u"ennemies": {'Bowser': 1, 'Koopa':50}, "epoch": now(),
                        }
        action.data = action.set_data(expected_data)
        action.save()

        self.assertEqual(expected_data, self.refresh(action).get_data())