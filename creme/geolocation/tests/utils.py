# -*- coding: utf-8 -*-

try:
    from creme.creme_core.models.setting_value import SettingValue
    from creme.persons.models import Organisation, Contact

    from ..constants import DEFAULT_SEPARATING_NEIGHBOURS
    from ..setting_keys import NEIGHBOURHOOD_DISTANCE

    from ..utils import get_setting, address_as_dict, addresses_from_persons, location_bounding_box
    from .base import GeoLocationBaseTestCase
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


__all__ = ('GeoLocationUtilsTestCase',)

class GeoLocationUtilsTestCase(GeoLocationBaseTestCase):
    def test_address_as_dict(self):
        self.login()

        orga = Organisation.objects.create(name='Orga 1', user=self.user)
        address = self.create_address(orga, zipcode='13012', town=u'Marseille', geoloc=(43.299991, 5.364832))

        self.assertDictEqual(dict(id=address.pk,
                                  address=u'13 rue du yahourt 13012 Marseille 13',
                                  name=u'Orga 1 - 13 rue du yahourt',
                                  latitude=43.299991,
                                  longitude=5.364832,
                                  draggable=True,
                                  geocoded=False,
                                  url=orga.get_absolute_url()), address_as_dict(address))

    def test_addresses_from_persons(self):
        self.login()

        orga = Organisation.objects.create(name='Orga 1', user=self.user)
        orga2 = Organisation.objects.create(name='Orga 2', user=self.user)
        contact = Contact.objects.create(last_name='Contact 1', user=self.user)

        orga_address = self.create_billing_address(orga, zipcode='13012', town=u'Marseille')
        self.create_shipping_address(orga, zipcode='01190', town=u'Ozan')
        self.create_address(orga, zipcode='01630', town=u'Péron')

        orga2_address = self.create_shipping_address(orga2, zipcode='01190', town=u'Ozan')
        self.create_address(orga2, zipcode='01630', town=u'Péron')

        contact_address = self.create_address(contact, zipcode='01630', town=u'Péron')

        self.assertListEqual(list(addresses_from_persons(Contact.objects.all(), self.user)),
                             [contact_address])

        self.assertListEqual(list(addresses_from_persons(Organisation.objects.all(), self.user)),
                             [orga_address, orga2_address])

    def test_get_setting(self):
        self.assertIsNone(get_setting('unknown'))
        self.assertEqual(get_setting('unknown', 12), 12)

        self.assertEqual(get_setting(NEIGHBOURHOOD_DISTANCE, DEFAULT_SEPARATING_NEIGHBOURS), DEFAULT_SEPARATING_NEIGHBOURS)

        SettingValue.create_if_needed(key=NEIGHBOURHOOD_DISTANCE, user=None, value=12500)
        self.assertEqual(get_setting(NEIGHBOURHOOD_DISTANCE, DEFAULT_SEPARATING_NEIGHBOURS), 12500)

    def test_location_bounding_box(self):
        # 10 km ~ 0.09046499004885108 lat, 0.12704038469036066 long (for 45° lat)
        self.assertEqual(((45.0 - 0.09046499004885108, 5.0 - 0.12704038469036066),
                          (45.0 + 0.09046499004885108, 5.0 + 0.12704038469036066)),
                         location_bounding_box(45.0, 5.0, 10000))

        # 10 km ~ 0.09046499004885108 lat, 0.09559627851921597 long (for 20° lat)
        self.assertEqual(((20.0 - 0.09046499004885108, 5.0 - 0.09559627851921597),
                          (20.0 + 0.09046499004885108, 5.0 + 0.09559627851921597)),
                         location_bounding_box(20.0, 5.0, 10000))
