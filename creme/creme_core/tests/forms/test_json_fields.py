# -*- coding: utf-8 -*-

try:
    from functools import partial
    from json import dumps as json_dump, loads as json_load

    from django.core.exceptions import ValidationError
    from django.contrib.contenttypes.models import ContentType
    from django.db.models.query import Q, QuerySet
    from django.urls import reverse
    from django.utils.translation import ugettext as _

    from .. import fake_forms
    from ..fake_models import FakeContact, FakeOrganisation, FakeImage
    from .base import FieldTestCase
    from creme.creme_core.auth import EntityCredentials
    from creme.creme_core.constants import REL_SUB_HAS
    from creme.creme_core.forms.fields import (JSONField,
            GenericEntityField, MultiGenericEntityField,
            RelationEntityField, MultiRelationEntityField,
            CreatorEntityField, MultiCreatorEntityField,
            FilteredEntityTypeField)
    from creme.creme_core.gui.quick_forms import quickforms_registry
    from creme.creme_core.models import (CremeProperty, CremePropertyType,
            RelationType, CremeEntity, EntityFilter, SetCredentials)
    from creme.creme_core.utils import creme_entity_content_types
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


class _JSONFieldBaseTestCase(FieldTestCase):
    def login_as_basic_user(self):
        user = self.login(is_superuser=False)

        SetCredentials.objects.create(role=self.role,
                                      value=EntityCredentials.VIEW | EntityCredentials.CHANGE |
                                            EntityCredentials.DELETE |
                                            EntityCredentials.LINK | EntityCredentials.UNLINK,
                                      set_type=SetCredentials.ESET_OWN,
                                     )

        return user

    # def create_contact(self, first_name='Eikichi', last_name='Onizuka', ptype=None, user=None, **kwargs):
    def create_contact(self, first_name='Eikichi', last_name='Onizuka', ptypes=(), user=None, **kwargs):
        contact = FakeContact.objects.create(user=user or self.user,
                                             first_name=first_name,
                                             last_name=last_name,
                                             **kwargs
                                            )

        # if ptype:
        #     CremeProperty.objects.create(type=ptype, creme_entity=contact)
        if ptypes:
            if isinstance(ptypes, CremePropertyType):
                ptypes = (ptypes,)

            for ptype in ptypes:
                CremeProperty.objects.create(type=ptype, creme_entity=contact)

        return contact

    def create_orga(self, name='Onibaku', user=None, **kwargs):
        user = user or self.user
        return FakeOrganisation.objects.create(user=user, name=name, **kwargs)

    # def create_loves_rtype(self, subject_ptype=None, object_ptype=None):
    #     subject_ptypes = (subject_ptype,) if subject_ptype else ()
    #     object_ptypes  = (object_ptype,) if object_ptype else ()
    def create_loves_rtype(self, subject_ptypes=(), object_ptypes=()):
        if isinstance(subject_ptypes, CremePropertyType):
            subject_ptypes = (subject_ptypes,)

        if isinstance(object_ptypes, CremePropertyType):
            object_ptypes = (object_ptypes,)

        return RelationType.create(('test-subject_loves', 'is loving', (), subject_ptypes),
                                   ('test-object_loves',  'loved by',  (), object_ptypes),
                                  )

    def create_hates_rtype(self):
        return RelationType.create(('test-subject_hates', 'is hating'),
                                   ('test-object_hates',  'hated by')
                                  )

    def create_employed_rtype(self):
        return RelationType.create(('test-subject_employed_by', u'is an employee of', [FakeContact]),
                                   ('test-object_employed_by',  u'employs',           [FakeOrganisation]),
                                  )

    def create_customer_rtype(self):
        return RelationType.create(('test-subject_customer', u'is a customer of', [FakeContact, FakeOrganisation]),
                                   ('test-object_customer',  u'is a supplier of', [FakeContact, FakeOrganisation]),
                                  )

    # def create_property_types(self):
    #     create_ptype = CremePropertyType.create
    #     return (create_ptype(str_pk='test-prop_strong', text='Is strong'),
    #             create_ptype(str_pk='test-prop_cute',   text='Is cute'),
    #            )


class JSONFieldTestCase(_JSONFieldBaseTestCase):
    def test_clean_empty_required(self):
        self.assertFieldValidationError(JSONField, 'required', JSONField(required=True).clean, None)

    def test_clean_empty_not_required(self):
        with self.assertNoException():
            JSONField(required=False).clean(None)

    def test_clean_invalid_json(self):
        clean = JSONField(required=True).clean

        self.assertFieldValidationError(JSONField, 'invalidformat', clean, '{"unclosed_dict"')
        self.assertFieldValidationError(JSONField, 'invalidformat', clean, '["unclosed_list",')
        self.assertFieldValidationError(JSONField, 'invalidformat', clean, '["","unclosed_str]')
        self.assertFieldValidationError(JSONField, 'invalidformat', clean, '["" "comma_error"]')

    def test_clean_valid(self):
        with self.assertNoException():
            JSONField(required=True).clean('{"ctype":"12","entity":"1"}')

    def test_clean_json_with_type(self):
        clean_json = JSONField(required=True).clean_json

        with self.assertNoException():
            clean_json('{"ctype":"12","entity":"1"}', dict)
            clean_json('125', int)
            clean_json('[125, 126]', list)

    def test_clean_json_invalid_type(self):
        clean = JSONField(required=True).clean_json

        self.assertFieldValidationError(JSONField, 'invalidtype', clean, '["a", "b"]', int)
        self.assertFieldValidationError(JSONField, 'invalidtype', clean, '["a", "b"]', dict)
        self.assertFieldValidationError(JSONField, 'invalidtype', clean, '152', list)

    def test_FMTing_to_json(self):
        self.assertEqual('', JSONField().from_python(''))

        val = 'this is a string'
        self.assertEqual(val, JSONField().from_python(val))

    def test_format_object_to_json(self):
        val = {'ctype': '12', 'entity': '1'}
        self.assertEqual(json_dump(val), JSONField().from_python(val))

    def test_clean_entity_from_model(self):
        self.login()
        contact = self.create_contact()
        field = JSONField(required=True)

        clean = field._clean_entity_from_model
        self.assertEqual(contact, clean(FakeContact, contact.pk))

        self.assertFieldValidationError(JSONField, 'doesnotexist', clean, FakeOrganisation, contact.pk)
        self.assertFieldValidationError(JSONField, 'doesnotexist', clean, FakeContact, 10000)

    def test_clean_filtered_entity_from_model(self):
        self.login()
        contact = self.create_contact()
        field = JSONField(required=True)

        clean = field._clean_entity_from_model
        self.assertEqual(contact, clean(FakeContact, contact.pk, qfilter=Q(pk=contact.pk)))
        self.assertFieldValidationError(JSONField, 'doesnotexist', clean, FakeContact, contact.pk, ~Q(pk=contact.pk))


class GenericEntityFieldTestCase(_JSONFieldBaseTestCase):
    # DATA_FORMAT = '{"ctype": {"create": "%s", "id": %s, "create_label": "%s"}, "entity": %s}'

    def build_field_data(self, ctype_id, entity_id, label=None):
        # return '{"ctype": {"create": "%(url)s", "id": %(ct_id)s, "create_label": "%(label)s"}, "entity": %(entity_id)s}' % {
        #     'url': reverse('creme_core__quick_form', args=(ctype_id,)),
        #     'ct_id': ctype_id,
        #     'label': label or ContentType.objects.get_for_id(ctype_id).model_class().creation_label,
        #     'entity_id': entity_id,
        # }
        return json_dump({
            'ctype': {
                    'create': reverse('creme_core__quick_form', args=(ctype_id,)),
                    'id': ctype_id,
                    'create_label': label or
                                    str(ContentType.objects.get_for_id(ctype_id).model_class().creation_label),
                },
            'entity': entity_id,
        })

    def test_models_ctypes(self):
        get_ct = ContentType.objects.get_for_model
        self.assertEqual([get_ct(FakeOrganisation), get_ct(FakeContact), get_ct(FakeImage)],
                         GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage]).get_ctypes()
                        )

    def test_default_ctypes(self):
        ctypes = GenericEntityField().get_ctypes()
        self.assertEqual(list(creme_entity_content_types()), ctypes)
        self.assertTrue(ctypes)

    def test_models_property(self):
        self.login()

        contact = self.create_contact()
        orga = self.create_orga('orga')

        ctype1 = contact.entity_type
        ctype2 = orga.entity_type

        field = GenericEntityField()
        self.assertEqual(list(), field.allowed_models)
        self.assertEqual(list(creme_entity_content_types()), field.get_ctypes())

        field.allowed_models = [FakeContact, FakeOrganisation]
        ctypes = list(field.get_ctypes())
        self.assertEqual(2, len(ctypes))
        self.assertIn(ctype1, ctypes)
        self.assertIn(ctype2, ctypes)

    def test_format_object(self):
        self.login()
        contact = self.create_contact()
        field = GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage])

        self.assertEqual(self.build_field_data(12, 1, 'Add'),
                         field.from_python({'ctype': {'create': reverse('creme_core__quick_form', args=(12,)),
                                                      'id': 12,
                                                      'create_label': 'Add',
                                                     },
                                            'entity': 1,
                                           })
                        )

        # No user info
        ct_id = contact.entity_type_id
        # NB: self.DATA_FORMAT/self.build_field_data() returns str with odd encoding, so we avoid them
        # self.assertEqual(self.DATA_FORMAT % ('',
        #                                      contact.entity_type_id,
        #                                      unicode(FakeContact.creation_label),
        #                                      contact.pk,
        #                                     ),
        self.assertEqual({'ctype': {'id': ct_id,
                                    'create': '',
                                    'create_label': _('Create a contact'),
                                   },
                          'entity': contact.id,
                         },
                         json_load(field.from_python(contact))
                        )

        field.user = self.user
        self.assertEqual({'ctype': {'id': ct_id,
                                    'create': reverse('creme_core__quick_form', args=(ct_id,)),
                                    'create_label': _('Create a contact'),
                                   },
                          'entity': contact.id,
                         },
                         json_load(field.from_python(contact))
                        )

    def test_clean_empty_required(self):
        clean = GenericEntityField(required=True).clean
        self.assertFieldValidationError(GenericEntityField, 'required', clean, None)
        self.assertFieldValidationError(GenericEntityField, 'required', clean, "{}")

    def test_clean_empty_not_required(self):
        with self.assertNoException():
            value = GenericEntityField(required=False).clean(None)

        self.assertIsNone(value)

    def test_clean_invalid_json(self):
        self.assertFieldValidationError(GenericEntityField, 'invalidformat',
                                        GenericEntityField(required=False).clean,
                                        '{"ctype":"12","entity":"1"'
                                       )

    def test_clean_invalid_data_type(self):
        clean = GenericEntityField(required=False).clean
        self.assertFieldValidationError(GenericEntityField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(GenericEntityField, 'invalidtype', clean, "[]")

    def test_clean_invalid_data(self):
        clean = GenericEntityField(required=False).clean
        self.assertFieldValidationError(GenericEntityField, 'invalidformat', clean, '{"ctype":"notadict","entity":"1"}')
        self.assertFieldValidationError(GenericEntityField, 'invalidformat', clean, '{"ctype":{"id": "notanumber", "create":""},"entity":"1"}')
        self.assertFieldValidationError(GenericEntityField, 'invalidformat', clean, '{"ctype":{"id": "12", "create":""},"entity":"notanumber"}')

    def test_clean_forbidden_ctype(self):
        self.login()

        contact = self.create_contact()
        self.assertFieldValidationError(GenericEntityField, 'ctypenotallowed',
                                        GenericEntityField(models=[FakeOrganisation, FakeImage]).clean,
                                        self.build_field_data(contact.entity_type_id, contact.id)
                                       )

    def test_clean_unknown_entity(self):
        self.login()
        contact = self.create_contact()
        ct_id = ContentType.objects.get_for_model(FakeImage).id  # Not Contact !!
        self.assertFieldValidationError(GenericEntityField, 'doesnotexist',
                                        GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage]).clean,
                                        self.build_field_data(ct_id, contact.pk)
                                       )

    def test_clean_deleted_entity(self):
        self.login()
        contact = self.create_contact(is_deleted=True)
        self.assertFieldValidationError(GenericEntityField, 'doesnotexist',
                                        GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage]).clean,
                                        self.build_field_data(contact.entity_type_id, contact.pk)
                                       )

    def test_clean_entity(self):
        user = self.login()
        contact = self.create_contact()

        with self.assertNumQueries(0):
            field = GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage])

        field.user = user
        self.assertEqual(contact, field.clean(self.build_field_data(contact.entity_type_id, contact.pk)))

    def test_clean_entity_old_format(self):
        user = self.login()
        contact = self.create_contact()
        field = GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage], user=user)
        self.assertEqual(contact, field.clean(json_dump({'ctype': str(contact.entity_type_id), 'entity': contact.id})))

    def test_clean_incomplete_not_required(self):
        user = self.login()
        contact = self.create_contact()

        clean = GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage], required=False, user=user).clean
        self.assertFieldValidationError(GenericEntityField, 'ctypenotallowed', clean,
                                        json_dump({'ctype': {'create': '', 'id': None}}),
                                       )
        self.assertIsNone(clean(json_dump({'ctype': {'create': '', 'id': str(contact.entity_type_id)}})))
        self.assertIsNone(clean(json_dump({'ctype': {'create': '', 'id': str(contact.entity_type_id)}, 'entity': None})))

    def test_clean_incomplete_required(self):
        "Required -> 'friendly' errors."
        self.login()
        contact = self.create_contact()

        clean = GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage], required=True).clean
        self.assertFieldValidationError(GenericEntityField, 'ctyperequired', clean,
                                        json_dump({'ctype': {'create': '', 'id': None}}),
                                       )
        self.assertFieldValidationError(GenericEntityField, 'entityrequired', clean,
                                        json_dump({'ctype': {'create': '', 'id': str(contact.entity_type_id)}}),
                                       )
        self.assertFieldValidationError(GenericEntityField, 'entityrequired', clean,
                                        json_dump({'ctype': {'create': '', 'id': str(contact.entity_type_id)}, 'entity': None}),
                                       )

    def test_autocomplete_property(self):
        field = GenericEntityField()
        self.assertFalse(field.autocomplete)

        field = GenericEntityField(autocomplete=True)
        self.assertTrue(field.autocomplete)

        field.autocomplete = False
        self.assertFalse(field.autocomplete)

    def test_clean_with_permission01(self):
        "Perm checking OK"
        user = self.login_as_basic_user()
        contact = self.create_contact()
        field = GenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage], user=user)
        self.assertEqual(contact, field.clean(self.build_field_data(contact.entity_type_id, contact.pk)))

    def test_clean_with_permission02(self):
        "Perm checking KO (LINK)"
        user = self.login_as_basic_user()

        contact = self.create_contact(user=self.other_user)
        field = GenericEntityField(models=[FakeOrganisation, FakeContact], user=user)

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_field_data(contact.entity_type_id, contact.pk))

        exception = cm.exception
        self.assertEqual('linknotallowed', exception.code)
        self.assertEqual(_(u'You are not allowed to link this entity: {}').format(
                                _(u'Entity #{id} (not viewable)').format(id=contact.id)
                            ),
                         exception.message
                        )

    def test_clean_with_permission03(self):
        "Perm checking: VIEW"
        user = self.login_as_basic_user()

        SetCredentials.objects.create(role=self.role,
                                      value=EntityCredentials.VIEW,
                                      set_type=SetCredentials.ESET_ALL,
                                      ctype=ContentType.objects.get_for_model(FakeContact),
                                     )

        contact = self.create_contact(user=self.other_user)
        orga    = self.create_orga(user=self.other_user)

        field = GenericEntityField(models=[FakeOrganisation, FakeContact], user=user,
                                   credentials=EntityCredentials.VIEW,
                                  )
        self.assertEqual(contact, field.clean(self.build_field_data(contact.entity_type_id, contact.pk)))

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_field_data(orga.entity_type_id, orga.pk))

        exception = cm.exception
        self.assertEqual('viewnotallowed', exception.code)
        self.assertEqual(_(u'You are not allowed to view this entity: {}').format(
                                _(u'Entity #{id} (not viewable)').format(id=orga.id)
                            ),
                         exception.message
                        )

    def test_clean_with_permission04(self):
        "Perm checking: CHANGE"
        user = self.login_as_basic_user()

        SetCredentials.objects.create(role=self.role,
                                      value=EntityCredentials.CHANGE,
                                      set_type=SetCredentials.ESET_ALL,
                                      ctype=ContentType.objects.get_for_model(FakeContact),
                                     )

        contact = self.create_contact(user=self.other_user)
        orga    = self.create_orga(user=self.other_user)

        field = GenericEntityField(models=[FakeOrganisation, FakeContact], user=user,
                                   credentials=EntityCredentials.CHANGE,
                                  )
        self.assertEqual(contact, field.clean(self.build_field_data(contact.entity_type_id, contact.pk)))

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_field_data(orga.entity_type_id, orga.pk))

        exception = cm.exception
        self.assertEqual('changenotallowed', exception.code)
        self.assertEqual(_(u'You are not allowed to edit this entity: {}').format(
                                _(u'Entity #{id} (not viewable)').format(id=orga.id)
                            ),
                         exception.message
                        )

    def test_clean_with_permission05(self):
        "Perm checking: perm combo"
        user = self.login_as_basic_user()

        get_ct = ContentType.objects.get_for_model
        create_sc = partial(SetCredentials.objects.create, role=self.role, set_type=SetCredentials.ESET_ALL)
        create_sc(value=EntityCredentials.VIEW, ctype=get_ct(FakeContact))
        create_sc(value=EntityCredentials.LINK, ctype=get_ct(FakeOrganisation))

        contact = self.create_contact(user=self.other_user)
        orga1 = self.create_orga(user=self.other_user)
        orga2 = self.create_orga()

        field = GenericEntityField(models=[FakeOrganisation, FakeContact], user=user,
                                   credentials=EntityCredentials.VIEW|EntityCredentials.LINK,
                                  )
        self.assertEqual(orga2, field.clean(self.build_field_data(orga2.entity_type_id, orga2.pk)))

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_field_data(orga1.entity_type_id, orga1.pk))
        self.assertEqual('viewnotallowed', cm.exception.code)

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_field_data(contact.entity_type_id, contact.pk))
        self.assertEqual('linknotallowed', cm.exception.code)


class MultiGenericEntityFieldTestCase(_JSONFieldBaseTestCase):
    # DATA_FORMAT = '{"ctype": {"create": "%s", "id": %s, "create_label": "%s"}, "entity": %s}'

    def _build_quick_forms_url(self, ct_id):
        return reverse('creme_core__quick_form', args=(ct_id,))

    # def build_field_entry_data(self, ctype_id, entity_id):
    #     return '{"ctype": {"create": "%(url)s", "id": %(ct_id)s, "create_label": "%(label)s"}, "entity": %(entity_id)s}' % {
    #         'url': reverse('creme_core__quick_form', args=(ctype_id,)),
    #         'ct_id': ctype_id,
    #         'label': ContentType.objects.get_for_id(ctype_id).model_class().creation_label,
    #         'entity_id': entity_id,
    #     }

    @classmethod
    def build_entry(cls, ctype_id, entity_id):
        return {
            'ctype':  {
                'create': reverse('creme_core__quick_form', args=(ctype_id,)),
                'id': ctype_id,
                'create_label': str(
                    ContentType.objects.get_for_id(ctype_id)
                               .model_class()
                               .creation_label
                ),
            },
            'entity': entity_id,
        }

    @classmethod
    def build_data(cls, *entities):
        return json_dump([cls.build_entry(entity.entity_type_id, entity.id) for entity in entities])

    def test_models_ctypes(self):
        get_ct = ContentType.objects.get_for_model
        models = [FakeOrganisation, FakeContact, FakeImage]
        self.assertEqual([get_ct(model) for model in models],
                         MultiGenericEntityField(models=models).get_ctypes()
                        )

    def test_default_ctypes(self):
        ctypes = MultiGenericEntityField().get_ctypes()
        self.assertEqual(list(creme_entity_content_types()), ctypes)
        self.assertTrue(ctypes)

    def test_format_object(self):
        user = self.login()

        contact = self.create_contact()
        orga    = self.create_orga()

        contact_ct_id = contact.entity_type_id
        orga_ct_id    = orga.entity_type_id

        contact_label = FakeContact.creation_label
        orga_label    = FakeOrganisation.creation_label

        build_url = self._build_quick_forms_url

        def build_entry_v1(ctype_id, entity_id, label):
            return {'ctype': {'create': reverse('creme_core__quick_form', args=(ctype_id,)),
                              'id': ctype_id,
                              'create_label': label,
                             },
                    'entity': entity_id,
                   }

        field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage])
        self.assertEqual([build_entry_v1(contact_ct_id, 1, contact_label),
                          build_entry_v1(orga_ct_id, 5,    orga_label),
                         ],
                         json_load(field.from_python([
                             {'ctype': {'id': contact_ct_id,
                                        'create': build_url(contact_ct_id) ,
                                        'create_label': str(contact_label)},
                                        'entity': 1,
                                       },
                             {'ctype': {'id': orga_ct_id,
                                        'create': build_url(orga_ct_id),
                                        'create_label': str(orga_label)},
                                        'entity': 5,
                                       },
                         ]))
                        )

        # No user
        def build_entry_v2(ctype_id, entity_id, label):
            return {'ctype': {'create': '',
                              'id': ctype_id,
                              'create_label': label,
                             },
                    'entity': entity_id,
                   }
        self.assertEqual([build_entry_v2(contact_ct_id, contact.id, contact_label),
                          build_entry_v2(orga_ct_id,    orga.id,    orga_label),
                         ],
                         json_load(field.from_python([contact, orga]))
                        )

        # With user
        def build_entry_v3(ctype_id, entity_id, label):
            return {'ctype': {'create': reverse('creme_core__quick_form', args=(ctype_id,)),
                              'id': ctype_id,
                              'create_label': label,
                             },
                    'entity': entity_id,
                   }

        field.user = user
        self.assertEqual([build_entry_v3(contact_ct_id, contact.id, contact_label),
                          build_entry_v3(orga_ct_id,    orga.id,    orga_label),
                         ],
                         json_load(field.from_python([contact, orga]))
                        )

    def test_clean_empty_required(self):
        clean = MultiGenericEntityField(required=True).clean
        self.assertFieldValidationError(MultiGenericEntityField, 'required', clean, None)
        self.assertFieldValidationError(MultiGenericEntityField, 'required', clean, "[]")

    def test_clean_empty_not_required(self):
        with self.assertNoException():
            val = MultiGenericEntityField(required=False).clean(None)

        self.assertEqual([], val)

    def test_clean_invalid_json(self):
        clean = MultiGenericEntityField(required=False).clean
        self.assertFieldValidationError(MultiGenericEntityField, 'invalidformat',
                                        clean, '{"ctype":"12","entity":"1"',
                                       )

    def test_clean_invalid_data_type(self):
        clean = MultiGenericEntityField(required=False).clean
        self.assertFieldValidationError(MultiGenericEntityField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(MultiGenericEntityField, 'invalidtype', clean, "{}")

    def test_clean_invalid_data(self):
        clean = MultiGenericEntityField(required=False).clean
        self.assertFieldValidationError(MultiGenericEntityField, 'invalidformat', clean, '[{"ctype":"notadict","entity":"1"}]')
        self.assertFieldValidationError(MultiGenericEntityField, 'invalidformat', clean, '[{"ctype":{"id": "notanumber", "create": ""},"entity":"1"}]')
        self.assertFieldValidationError(MultiGenericEntityField, 'invalidformat', clean, '[{"ctype":{"id": "12", "create": ""},"entity":"notanumber"}]')

    def test_clean_forbidden_ctype(self):
        self.login()

        clean = MultiGenericEntityField(models=[FakeOrganisation, FakeImage]).clean
        value = self.build_data(self.create_contact(), self.create_orga())
        self.assertFieldValidationError(MultiGenericEntityField, 'ctypenotallowed', clean, value)

    def test_clean_unknown_entity(self):
        self.login()
        contact1   = self.create_contact()
        contact2   = self.create_contact(first_name='Ryuji', last_name='Danma')
        ct_orga_id = ContentType.objects.get_for_model(FakeOrganisation).id

        field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact, FakeImage])
        value = json_dump([self.build_entry(contact1.entity_type_id, contact1.id),
                           self.build_entry(ct_orga_id,              contact2.id),
                         ])
        self.assertFieldValidationError(MultiGenericEntityField, 'doesnotexist', field.clean, value)

    def test_clean_deleted_entity(self):
        self.login()
        cls = MultiGenericEntityField
        contact = self.create_contact(is_deleted=True)
        clean = cls(models=[FakeOrganisation, FakeContact, FakeImage]).clean
        self.assertFieldValidationError(cls, 'doesnotexist', clean, self.build_data(contact))

    def test_clean_entities(self):
        user = self.login()
        contact = self.create_contact()
        orga    = self.create_orga()

        with self.assertNumQueries(0):
            field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact])

        field.user = user
        self.assertEqual([contact, orga], field.clean(self.build_data(contact, orga)))

    def test_clean_entities_old_format(self):
        user = self.login()
        contact = self.create_contact()
        orga    = self.create_orga()

        field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact], user=user)
        value = json_dump([{'ctype': str(contact.entity_type_id), 'entity': contact.id},
                           {'ctype': str(orga.entity_type_id),    'entity': orga.id},
                          ])

        self.assertEqual([contact, orga], field.clean(value))

    def test_clean_duplicates(self):
        "Duplicates are removed"
        user = self.login()
        contact = self.create_contact()
        orga    = self.create_orga()

        field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact])
        field.user = user
        value = self.build_data(contact, orga, contact)  # 'contact' x 2

        # Contact once
        self.assertEqual([contact, orga], field.clean(value))

    def test_clean_duplicates_no_unique(self):
        "Duplicates are allowed"
        user = self.login()
        contact = self.create_contact()
        orga    = self.create_orga()

        field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact], unique=False, user=user)
        value = self.build_data(contact, orga, contact)  # 'contact' x 2

        # Contact twice
        self.assertEqual([contact, orga, contact], field.clean(value))

    def test_clean_incomplete_not_required(self):
        "Not required"
        user = self.login()
        contact = self.create_contact()
        orga    = self.create_orga()

        clean = MultiGenericEntityField(models=[FakeOrganisation, FakeContact], required=False, user=user).clean

        ct_id = str(contact.entity_type_id)
        self.assertEqual([], clean(json_dump([{'ctype': {'id': ct_id}}])))
        self.assertEqual([], clean(json_dump([{'ctype': {'id': ct_id}, 'entity': None}])))

        self.assertEqual([contact, orga], 
                         clean(json_dump([
                                    {'ctype': {'id': ct_id}},
                                    {'ctype': {'id': ct_id}, 'entity': None},
                                    {'ctype': {'id': ct_id}, 'entity': str(contact.id)},
                                    {'ctype': {'id': str(orga.entity_type_id)}, 'entity': str(orga.pk)},
                               ])
                         )
                        )

    def test_clean_incomplete_required(self):
        "Required -> 'friendly' errors :)"
        user = self.login()
        contact = self.create_contact()
        orga    = self.create_orga()

        clean = MultiGenericEntityField(models=[FakeOrganisation, FakeContact], required=True, user=user).clean
        ct_id = str(contact.entity_type_id)
        self.assertFieldValidationError(RelationEntityField, 'required', clean,
                                        json_dump([{'ctype': {'id': ct_id}},
                                                   {'ctype': {'id': ct_id}, 'entity': None},
                                                  ])
                                       )
        self.assertEqual([contact, orga],
                         clean(json_dump([
                             {'ctype': {'id': ct_id}},
                             {'ctype': {'id': ct_id}, 'entity': None},
                             {'ctype': {'id': ct_id}, 'entity': str(contact.id)},
                             {'ctype': {'id': str(orga.entity_type_id)}, 'entity': str(orga.pk)},
                         ])
                         )
                        )

    def test_clean_with_permission01(self):
        "Perm checking OK"
        user = self.login_as_basic_user()
        contact = self.create_contact()
        orga = self.create_orga()
        field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact], user=user)

        self.assertEqual([contact, orga],
                         field.clean(self.build_data(contact, orga))
                        )

    def test_clean_with_permission02(self):
        "Perm checking KO"
        user = self.login_as_basic_user()
        contact = self.create_contact()
        orga = self.create_orga(user=self.other_user)
        field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact], user=user)

        with self.assertRaises(ValidationError) as cm:
            field.clean(field.clean(self.build_data(contact, orga)))

        exception = cm.exception
        self.assertEqual('linknotallowed', exception.code)
        self.assertEqual(_(u'Some entities are not linkable: {}').format(
                                _(u'Entity #{id} (not viewable)').format(id=orga.id)
                            ),
                         exception.message
                        )

    def test_clean_with_permission03(self):
        "Perm checking: perm combo"
        user = self.login_as_basic_user()

        get_ct = ContentType.objects.get_for_model
        create_sc = partial(SetCredentials.objects.create, role=self.role, set_type=SetCredentials.ESET_ALL)
        create_sc(value=EntityCredentials.VIEW, ctype=get_ct(FakeContact))
        create_sc(value=EntityCredentials.LINK, ctype=get_ct(FakeOrganisation))

        contact = self.create_contact(user=self.other_user)
        orga1 = self.create_orga(user=self.other_user)
        orga2 = self.create_orga()

        field = MultiGenericEntityField(models=[FakeOrganisation, FakeContact], user=user,
                                        credentials=EntityCredentials.VIEW|EntityCredentials.LINK,
                                       )

        self.assertEqual([orga2], field.clean(self.build_data(orga2)))

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_data(orga1))
        self.assertEqual('viewnotallowed', cm.exception.code)

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_data(contact))
        self.assertEqual('linknotallowed', cm.exception.code)

    def test_autocomplete_property(self):
        with self.assertNumQueries(0):
            field = MultiGenericEntityField()

        self.assertFalse(field.autocomplete)

        field = MultiGenericEntityField(autocomplete=True)
        self.assertTrue(field.autocomplete)

        field.autocomplete = False
        self.assertFalse(field.autocomplete)


class RelationEntityFieldTestCase(_JSONFieldBaseTestCase):
    # FMT = '{"rtype": "%s", "ctype": "%s", "entity": "%s"}'

    @staticmethod
    def build_data(rtype_id, entity):
        return json_dump({'rtype':  rtype_id,
                          'ctype':  str(entity.entity_type_id),
                          'entity': str(entity.id),
                         })

    def test_rtypes(self):
        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        with self.assertNumQueries(0):
            field = RelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id])

        rtypes = list(field._get_allowed_rtypes_objects())
        self.assertEqual(2, len(rtypes))
        self.assertIn(rtype1, rtypes)
        self.assertIn(rtype2, rtypes)

        rtypes_ids = list(field._get_allowed_rtypes_ids())
        self.assertEqual(2, len(rtypes_ids))
        self.assertIn(rtype1.id, rtypes_ids)
        self.assertIn(rtype2.id, rtypes_ids)

    def test_rtypes_queryset(self):
        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        with self.assertNumQueries(0):
            field = RelationEntityField(
                        allowed_rtypes=RelationType.objects
                                                   .filter(pk__in=[rtype1.id, rtype2.id])
                     )

        rtypes = list(field._get_allowed_rtypes_objects())
        self.assertEqual(2, len(rtypes))
        self.assertIn(rtype1, rtypes)
        self.assertIn(rtype2, rtypes)

        rtypes_ids = list(field._get_allowed_rtypes_ids())
        self.assertEqual(2, len(rtypes_ids))
        self.assertIn(rtype1.id, rtypes_ids)
        self.assertIn(rtype2.id, rtypes_ids)

    def test_rtypes_queryset_changes(self):
        rtype2 = self.create_hates_rtype()[0]

        field = RelationEntityField(allowed_rtypes=RelationType.objects.filter(pk__in=["test-subject_loves", rtype2.id]))
        rtypes = list(field._get_allowed_rtypes_objects())
        self.assertEqual(1, len(rtypes))
        self.assertIn(rtype2, rtypes)

        rtype1 = self.create_loves_rtype()[0]

        rtypes_ids = list(field._get_allowed_rtypes_ids())
        self.assertEqual(2, len(rtypes_ids))
        self.assertIn(rtype1.id, rtypes_ids)
        self.assertIn(rtype2.id, rtypes_ids)

        rtype2.delete()

        rtypes_ids = list(field._get_allowed_rtypes_ids())
        self.assertEqual(1, len(rtypes_ids))
        self.assertIn(rtype1.id, rtypes_ids)

    def test_default_rtypes(self):
        self.assertEqual([RelationType.objects.get(pk=REL_SUB_HAS)],
                         list(RelationEntityField()._get_allowed_rtypes_objects())
                        )

    def test_rtypes_property(self):
        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        field = RelationEntityField()
        self.assertTrue(isinstance(field.allowed_rtypes, QuerySet))
        self.assertEqual([RelationType.objects.get(pk=REL_SUB_HAS)],
                         list(field.allowed_rtypes)
                        )
        self.assertEqual([REL_SUB_HAS], list(field._get_allowed_rtypes_ids()))
        self.assertEqual([RelationType.objects.get(pk=REL_SUB_HAS)],
                         list(field._get_allowed_rtypes_objects())
                        )

        field.allowed_rtypes = [rtype1.id, rtype2.id] # <===
        rtypes = list(field._get_allowed_rtypes_objects())
        self.assertEqual(2, len(rtypes))
        self.assertIn(rtype1, rtypes)
        self.assertIn(rtype2, rtypes)

    def test_rtypes_queryset_property(self):
        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        field = RelationEntityField()
        self.assertTrue(isinstance(field.allowed_rtypes, QuerySet))
        self.assertEqual([RelationType.objects.get(pk=REL_SUB_HAS)],
                         list(field.allowed_rtypes)
                        )
        self.assertEqual([REL_SUB_HAS], list(field._get_allowed_rtypes_ids()))
        self.assertEqual([RelationType.objects.get(pk=REL_SUB_HAS)],
                         list(field._get_allowed_rtypes_objects())
                        )

        field.allowed_rtypes = RelationType.objects.filter(pk__in=[rtype1.id, rtype2.id]) # <===
        rtypes = list(field._get_allowed_rtypes_objects())
        self.assertEqual(2, len(rtypes))
        self.assertIn(rtype1, rtypes)
        self.assertIn(rtype2, rtypes)

    def test_clean_empty_required(self):
        clean = RelationEntityField(required=True).clean
        self.assertFieldValidationError(RelationEntityField, 'required', clean, None)
        self.assertFieldValidationError(RelationEntityField, 'required', clean, "{}")

    def test_clean_empty_not_required(self):
        self.assertIsNone(RelationEntityField(required=False).clean(None))

    def test_clean_invalid_json(self):
        self.assertFieldValidationError(RelationEntityField, 'invalidformat',
                                        RelationEntityField(required=False).clean,
                                        '{"rtype":"10", "ctype":"12","entity":"1"'
                                       )

    def test_clean_invalid_data_type(self):
        clean = RelationEntityField(required=False).clean
        self.assertFieldValidationError(RelationEntityField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(RelationEntityField, 'invalidtype', clean, '"[]"')

    def test_clean_invalid_data(self):
        clean = RelationEntityField(required=False).clean
        self.assertFieldValidationError(RelationEntityField, 'invalidformat', clean, '{"rtype":"notanumber", ctype":"12","entity":"1"}')
        self.assertFieldValidationError(RelationEntityField, 'invalidformat', clean, '{"rtype":"10", ctype":"notanumber","entity":"1"}')
        self.assertFieldValidationError(RelationEntityField, 'invalidformat', clean, '{"rtype":"10", "ctype":"12","entity":"notanumber"}')

    def test_clean_unknown_rtype(self):
        self.login()
        contact = self.create_contact()

        rtype_id1 = 'test-i_do_not_exist'
        rtype_id2 = 'test-neither_do_i'

        # Message changes cause unknown rtype is ignored in allowed list
        self.assertFieldValidationError(
                RelationEntityField, 'rtypenotallowed',
                RelationEntityField(allowed_rtypes=[rtype_id1, rtype_id2]).clean,
                self.build_data(rtype_id1, contact)
            )

    def test_clean_not_allowed_rtype(self):
        self.login()
        contact = self.create_contact()

        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]
        rtype3 = RelationType.create(('test-subject_friend', 'is friend of'), ('test-object_friend', 'has friend'))[0]

        self.assertFieldValidationError(
                RelationEntityField, 'rtypenotallowed',
                RelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id]).clean,
                self.build_data(rtype3.id, contact)
            )

    def test_clean_not_allowed_rtype_queryset(self):
        self.login()
        contact = self.create_contact()

        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]
        rtype3 = RelationType.create(('test-subject_friend', 'is friend of'),
                                     ('test-object_friend', 'has friend')
                                    )[0]

        self.assertFieldValidationError(
                RelationEntityField, 'rtypenotallowed',
                RelationEntityField(allowed_rtypes=RelationType.objects.filter(pk__in=[rtype1.id, rtype2.id])).clean,
                self.build_data(rtype3.id, contact)
            )

    def test_clean_ctype_constraint_error(self):
        self.login()
        orga = self.create_orga()

        rtype1 = self.create_employed_rtype()[1]
        rtype2 = self.create_customer_rtype()[1]
        self.assertFieldValidationError(
                RelationEntityField, 'ctypenotallowed',
                RelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id]).clean,
                self.build_data(rtype1.id, orga)  # <= needs a Contact
            )

    def test_clean_unknown_entity(self):
        self.login()
        orga = self.create_orga()

        rtype1 = self.create_employed_rtype()[1]
        rtype2 = self.create_customer_rtype()[1]
        ct_contact_id = ContentType.objects.get_for_model(FakeContact).id
        self.assertFieldValidationError(
                RelationEntityField, 'doesnotexist',
                RelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id]).clean,
                # self.FMT % (rtype1.id, ct_contact_id, orga.pk)
                json_dump({'rtype':  rtype1.id,
                           'ctype':  str(ct_contact_id),
                           'entity': str(orga.id),
                           })
            )

    def test_clean_deleted_entity(self):
        self.login()
        orga = self.create_orga(is_deleted=True)
        rtype1 = self.create_employed_rtype()[0]
        rtype2 = self.create_customer_rtype()[0]
        self.assertFieldValidationError(
                RelationEntityField, 'doesnotexist',
                RelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id]).clean,
                self.build_data(rtype1.id, orga)
            )

    def test_clean_relation(self):
        user = self.login()
        contact = self.create_contact()
        rtype1 = self.create_employed_rtype()[1]
        rtype2 = self.create_customer_rtype()[1]

        field = RelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id])
        field.user = user
        self.assertEqual((rtype1, contact),
                         field.clean(self.build_data(rtype1.id, contact))
                        )

    def test_clean_ctype_without_constraint(self):
        user = self.login()
        contact = self.create_contact()
        rtype = self.create_loves_rtype()[0]

        field = RelationEntityField(allowed_rtypes=[rtype.id], user=user)
        self.assertEqual((rtype, contact),
                         field.clean(self.build_data(rtype.id, contact))
                        )

    def test_clean_properties_constraint_error(self):
        user = self.login()
        # subject_ptype, object_ptype = self.create_property_types()

        create_ptype = CremePropertyType.create
        ptype1 = create_ptype(str_pk='test-prop_strong', text='Is strong')
        ptype2 = create_ptype(str_pk='test-prop_cute',   text='Is cute')
        ptype3 = create_ptype(str_pk='test-prop_smart',  text='Is smart')

        # rtype = self.create_loves_rtype(subject_ptype=subject_ptype, object_ptype=object_ptype)[0]
        rtype = self.create_loves_rtype(object_ptypes=(ptype1, ptype2))[0]
        contact = self.create_contact(ptypes=(ptype1, ptype3))  # <= does not have the property 'ptype2'

        self.assertFieldValidationError(RelationEntityField, 'nopropertymatch',
                                        RelationEntityField(allowed_rtypes=[rtype.pk], user=user).clean,
                                        self.build_data(rtype.id, contact)
                                       )

    def test_clean_properties_constraint(self):
        user = self.login()
        # subject_ptype, object_ptype = self.create_property_types()

        create_ptype = CremePropertyType.create
        ptype1 = create_ptype(str_pk='test-prop_strong', text='Is strong')
        ptype2 = create_ptype(str_pk='test-prop_cute',   text='Is cute')
        ptype3 = create_ptype(str_pk='test-prop_smart',  text='Is smart')

        # rtype = self.create_loves_rtype(subject_ptype=subject_ptype, object_ptype=object_ptype)[0]
        rtype = self.create_loves_rtype(object_ptypes=(ptype1, ptype2))[0]
        # contact = self.create_contact(ptype=object_ptype)  # <= has the property
        contact = self.create_contact(ptypes=(ptype1, ptype2, ptype3))  # <= has all the properties

        field = RelationEntityField(allowed_rtypes=[rtype.id], user=user)
        self.assertEqual((rtype, contact),
                         field.clean(self.build_data(rtype.id, contact))
                        )

    def test_clean_with_permission01(self):
        "Perm checking OK"
        user = self.login_as_basic_user()
        contact = self.create_contact()
        rtype = self.create_loves_rtype()[0]

        field = RelationEntityField(allowed_rtypes=[rtype.id], user=user)
        self.assertEqual((rtype, contact),
                         field.clean(self.build_data(rtype.id, contact))
                        )

    def test_clean_with_permission02(self):
        "Perm checking KO"
        user = self.login_as_basic_user()
        contact = self.create_contact(user=self.other_user)
        rtype = self.create_loves_rtype()[0]

        field = RelationEntityField(allowed_rtypes=[rtype.id], user=user)

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_data(rtype.id, contact))

        self.assertEqual('linknotallowed', cm.exception.code)

    def test_clean_incomplete01(self):
        'Not required'
        self.login()
        rtype = self.create_loves_rtype()[0]
        contact = self.create_contact()

        clean = RelationEntityField(required=False).clean
        self.assertIsNone(clean(json_dump({'rtype': rtype.id})))
        self.assertIsNone(clean(json_dump({'rtype': rtype.id, 'ctype': str(contact.entity_type_id)})))

    def test_clean_incomplete02(self):
        "Required -> 'friendly' errors."
        self.login()
        rtype = self.create_loves_rtype()[0]
        contact = self.create_contact()

        clean = RelationEntityField(required=True).clean
        self.assertFieldValidationError(RelationEntityField, 'ctyperequired', clean,
                                        json_dump({'rtype': rtype.id})
                                       )
        self.assertFieldValidationError(RelationEntityField, 'entityrequired', clean,
                                        json_dump({'rtype': rtype.id, 'ctype': str(contact.entity_type_id)})
                                       )

    def test_autocomplete_property(self):
        field = RelationEntityField()
        self.assertFalse(field.autocomplete)

        field = RelationEntityField(autocomplete=True)
        self.assertTrue(field.autocomplete)

        field.autocomplete = False
        self.assertFalse(field.autocomplete)


class MultiRelationEntityFieldTestCase(_JSONFieldBaseTestCase):
    # TODO: factorise
    @classmethod
    def build_entry(cls, rtype_id, ctype_id, entity_id):
        return {'rtype':  rtype_id,
                'ctype':  str(ctype_id),
                'entity': str(entity_id),
               }

    @classmethod
    def build_data(cls, *relations):
        return json_dump([
            cls.build_entry(rtype_id, entity.entity_type_id, entity.id)
                for rtype_id, entity in relations
        ])

    def test_rtypes(self):
        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        with self.assertNumQueries(0):
            field = MultiRelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id])

        rtypes = list(field._get_allowed_rtypes_objects())
        self.assertEqual(2, len(rtypes))
        self.assertIn(rtype1, rtypes)
        self.assertIn(rtype2, rtypes)

    def test_rtypes_queryset(self):
        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        with self.assertNumQueries(0):
            field = MultiRelationEntityField(
                        allowed_rtypes=RelationType.objects
                                                   .filter(pk__in=[rtype1.id, rtype2.id])
                     )

        rtypes = list(field._get_allowed_rtypes_objects())
        self.assertEqual(2, len(rtypes))
        self.assertIn(rtype1, rtypes)
        self.assertIn(rtype2, rtypes)

        rtypes_ids = list(field._get_allowed_rtypes_ids())
        self.assertEqual(2, len(rtypes_ids))
        self.assertIn(rtype1.id, rtypes_ids)
        self.assertIn(rtype2.id, rtypes_ids)

    def test_rtypes_queryset_changes(self):
        rtype2 = self.create_hates_rtype()[0]

        field = MultiRelationEntityField(allowed_rtypes=RelationType.objects.filter(pk__in=["test-subject_loves", rtype2.id]))
        rtypes = list(field._get_allowed_rtypes_objects())
        self.assertEqual(1, len(rtypes))
        self.assertIn(rtype2, rtypes)

        rtype1 = self.create_loves_rtype()[0]

        rtypes_ids = list(field._get_allowed_rtypes_ids())
        self.assertEqual(2, len(rtypes_ids))
        self.assertIn(rtype1.id, rtypes_ids)
        self.assertIn(rtype2.id, rtypes_ids)

        rtype2.delete()

        rtypes_ids = list(field._get_allowed_rtypes_ids())
        self.assertEqual(1, len(rtypes_ids))
        self.assertIn(rtype1.id, rtypes_ids)

    def test_default_rtypes(self):
        self.assertEqual([RelationType.objects.get(pk=REL_SUB_HAS)],
                         list(MultiRelationEntityField()._get_allowed_rtypes_objects())
                        )

    def test_clean_empty_required(self):
        clean = MultiRelationEntityField(required=True).clean
        self.assertFieldValidationError(MultiRelationEntityField, 'required', clean, None)
        self.assertFieldValidationError(MultiRelationEntityField, 'required', clean, "[]")

    def test_clean_empty_not_required(self):
        MultiRelationEntityField(required=False).clean(None)

    def test_clean_invalid_json(self):
        field = MultiRelationEntityField(required=False)
        self.assertFieldValidationError(MultiRelationEntityField, 'invalidformat', field.clean, '{"rtype":"10", "ctype":"12","entity":"1"')

    def test_clean_invalid_data_type(self):
        clean = MultiRelationEntityField(required=False).clean
        self.assertFieldValidationError(MultiRelationEntityField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(MultiRelationEntityField, 'invalidtype', clean, '"{}"')
        self.assertFieldValidationError(MultiRelationEntityField, 'invalidtype', clean, '{"rtype":"10", "ctype":"12","entity":"1"}')

    def test_clean_invalid_data(self):
        clean = MultiRelationEntityField(required=False).clean
        self.assertFieldValidationError(MultiRelationEntityField, 'invalidformat', clean, '[{"rtype":"notanumber", ctype":"12","entity":"1"}]')
        self.assertFieldValidationError(MultiRelationEntityField, 'invalidformat', clean, '[{"rtype":"10", ctype":"notanumber","entity":"1"}]')
        self.assertFieldValidationError(MultiRelationEntityField, 'invalidformat', clean, '[{"rtype":"10", "ctype":"12","entity":"notanumber"}]')

    def test_clean_unknown_rtype(self):
        self.login()
        contact = self.create_contact()

        rtype_id1 = 'test-i_do_not_exist'
        rtype_id2 = 'test-neither_do_i'

        self.assertFieldValidationError(
                MultiRelationEntityField, 'rtypenotallowed',
                MultiRelationEntityField(allowed_rtypes=[rtype_id1, rtype_id2]).clean,
                self.build_data([rtype_id1, contact])
            )

    def test_clean_not_allowed_rtype(self):
        self.login()
        contact = self.create_contact()
        orga    = self.create_orga()

        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]
        rtype3 = RelationType.create(('test-subject_friend', 'is friend of'),
                                     ('test-object_friend', 'has friend')
                                    )[0]

        self.assertFieldValidationError(
            MultiRelationEntityField, 'rtypenotallowed',
            MultiRelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id]).clean,
            self.build_data((rtype3.id, contact),
                            (rtype3.id, orga),
                           )
        )

    def test_clean_not_allowed_rtype_queryset(self):
        cls = MultiRelationEntityField
        self.login()
        contact = self.create_contact()
        orga    = self.create_orga()

        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]
        rtype3 = RelationType.create(('test-subject_friend', 'is friend of'),
                                     ('test-object_friend', 'has friend')
                                    )[0]

        self.assertFieldValidationError(
            cls, 'rtypenotallowed',
            cls(allowed_rtypes=RelationType.objects.filter(pk__in=[rtype1.id, rtype2.id])).clean,
            self.build_data((rtype3.id, contact),
                            (rtype3.id, orga),
                           )
        )

    def test_clean_ctype_constraint_error(self):
        self.login()
        contact = self.create_contact()
        orga = self.create_orga()

        rtype1 = self.create_employed_rtype()[1]
        rtype2 = self.create_customer_rtype()[1]

        self.assertFieldValidationError(
                MultiRelationEntityField, 'ctypenotallowed',
                MultiRelationEntityField(allowed_rtypes=[rtype2.id, rtype1.id]).clean,
                self.build_data((rtype1.id, orga),  # <= not a Contact
                                (rtype2.id, contact),
                               )
            )

    def test_clean_unknown_entity(self):
        self.login()
        contact = self.create_contact()
        orga = self.create_orga()

        rtype1 = self.create_employed_rtype()[1]
        rtype2 = self.create_customer_rtype()[1]

        self.assertFieldValidationError(
                MultiRelationEntityField, 'doesnotexist',
                MultiRelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id]).clean,
                json_dump([self.build_entry(rtype1.id, contact.entity_type_id, orga.id),  # <=== bad ctype !
                           self.build_entry(rtype2.id, contact.entity_type_id, contact.id),
                          ])
            )

    def test_clean_deleted_entity(self):
        self.login()
        contact = self.create_contact(is_deleted=True)

        rtype1 = self.create_employed_rtype()[1]
        rtype2 = self.create_customer_rtype()[1]

        self.assertFieldValidationError(
                MultiRelationEntityField, 'doesnotexist',
                MultiRelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id]).clean,
                self.build_data([rtype1.id, contact])
            )

    def test_clean_relations(self):
        user = self.login()
        contact = self.create_contact()
        orga = self.create_orga()

        rtype_employed, rtype_employs = self.create_employed_rtype()
        rtype_supplier = self.create_customer_rtype()[1]

        field = MultiRelationEntityField(allowed_rtypes=[rtype_supplier.id, rtype_employs.id, rtype_employed.id])
        field.user = user
        self.assertEqual([(rtype_employs, contact), (rtype_supplier, contact), (rtype_employed, orga)],
                         field.clean(self.build_data((rtype_employs.id,  contact),
                                                     (rtype_supplier.id, contact),
                                                     (rtype_employed.id, orga),
                                                    )
                                    )
                        )

    def test_clean_relations_queryset(self):
        user = self.login()
        contact = self.create_contact()
        orga = self.create_orga()

        rtype_employed, rtype_employs = self.create_employed_rtype()
        rtype_supplier = self.create_customer_rtype()[1]

        field = MultiRelationEntityField(allowed_rtypes=RelationType.objects.filter(pk__in=[rtype_supplier.id,
                                                                                            rtype_employs.id,
                                                                                            rtype_employed.id,
                                                                                           ]
                                                                                   ),
                                         user=user,
                                        )
        self.assertEqual([(rtype_employs, contact), (rtype_supplier, contact), (rtype_employed, orga)],
                         field.clean(self.build_data((rtype_employs.id,  contact),
                                                     (rtype_supplier.id, contact),
                                                     (rtype_employed.id, orga),
                                                    )
                                    )
                        )

    def test_clean_ctype_without_constraint(self):
        user = self.login()
        contact = self.create_contact()
        rtype = self.create_loves_rtype()[0]

        field = MultiRelationEntityField(allowed_rtypes=[rtype.id], user=user)
        self.assertEqual([(rtype, contact)],
                         field.clean(self.build_data([rtype.id, contact]))
                        )

    def test_clean_properties_constraint_error(self):
        user = self.login()
        # subject_ptype, object_ptype = self.create_property_types()

        create_ptype = CremePropertyType.create
        ptype1 = create_ptype(str_pk='test-prop_strong', text='Is strong')
        ptype2 = create_ptype(str_pk='test-prop_cute',   text='Is cute')
        ptype3 = create_ptype(str_pk='test-prop_smart',  text='Is smart')

        # rtype_constr    = self.create_loves_rtype(subject_ptype=subject_ptype, object_ptype=object_ptype)[0]
        rtype_constr    = self.create_loves_rtype(object_ptypes=(ptype1, ptype2))[0]
        rtype_no_constr = self.create_hates_rtype()[0]

        # contact = self.create_contact()  # <= does not have the property
        contact = self.create_contact(ptypes=(ptype1, ptype3))  # <= does not have the property 'ptype2'
        orga = self.create_orga()

        field = MultiRelationEntityField(allowed_rtypes=[rtype_constr.pk, rtype_no_constr.pk], user=user)
        self.assertFieldValidationError(MultiRelationEntityField, 'nopropertymatch', field.clean,
                                        self.build_data((rtype_constr.id,    contact),
                                                        (rtype_no_constr.id, orga),
                                                       )
                                       )

    def test_clean_properties_constraint(self):
        user = self.login()
        # subject_ptype, object_ptype = self.create_property_types()

        create_ptype = CremePropertyType.create
        ptype1 = create_ptype(str_pk='test-prop_strong', text='Is strong')
        ptype2 = create_ptype(str_pk='test-prop_cute',   text='Is cute')
        ptype3 = create_ptype(str_pk='test-prop_smart',  text='Is smart')

        # rtype_constr    = self.create_loves_rtype(subject_ptype=subject_ptype, object_ptype=object_ptype)[0]
        rtype_constr    = self.create_loves_rtype(object_ptypes=(ptype1, ptype2))[0]
        rtype_no_constr = self.create_hates_rtype()[0]

        # contact = self.create_contact(ptype=object_ptype)  # <= has the property
        contact = self.create_contact(ptypes=(ptype1, ptype3, ptype2))  # <= has all the properties
        orga = self.create_orga()

        field = MultiRelationEntityField(allowed_rtypes=[rtype_constr.pk, rtype_no_constr.pk])
        field.user = user
        self.assertEqual([(rtype_constr, contact), (rtype_no_constr, orga)],
                         field.clean(self.build_data((rtype_constr.pk,    contact),
                                                     (rtype_no_constr.pk, orga),
                                                    )
                                    )
                        )

    def test_clean_incomplete01(self):
        "Not required"
        user = self.login()
        rtype = self.create_loves_rtype()[0]
        contact = self.create_contact()

        clean = MultiRelationEntityField(required=False, allowed_rtypes=[rtype.id], user=user).clean
        self.assertEqual([], clean(json_dump([{'rtype': rtype.id}])))

        ct_id = str(contact.entity_type_id)
        self.assertEqual([], clean(json_dump([{'rtype': rtype.id, 'ctype': ct_id}])))
        self.assertEqual([(rtype, contact)],
                         clean(json_dump([{'rtype': rtype.id, 'ctype': ct_id},
                                          {'rtype': rtype.id, 'ctype': ct_id, 'entity': str(contact.id)},
                                          {'rtype': rtype.id}])
                              )
                        )

    def test_clean_incomplete02(self):
        "Required -> 'friendly' errors :)"
        user = self.login()
        rtype  = self.create_loves_rtype()[0]
        contact = self.create_contact()

        clean = MultiRelationEntityField(required=True, allowed_rtypes=[rtype.id], user=user).clean
        ct_id = str(contact.entity_type_id)
        self.assertFieldValidationError(RelationEntityField, 'required', clean,
                                        json_dump([{'rtype': rtype.id, 'ctype': ct_id},
                                                   {'rtype': rtype.id}
                                                  ])
                                       )
        self.assertEqual([(rtype, contact)],
                         clean(json_dump([{'rtype': rtype.id, 'ctype': ct_id},
                                          {'rtype': rtype.id, 'ctype': ct_id, 'entity': str(contact.id)},
                                          {'rtype': rtype.id},
                                         ])
                              )
                        )

    def test_clean_with_permission01(self):
        "Perm checking OK"
        user = self.login_as_basic_user()
        contact = self.create_contact()
        orga    = self.create_orga()

        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        field = MultiRelationEntityField(required=True, allowed_rtypes=[rtype1.id,rtype2.id])
        field.user = user
        self.assertEqual([(rtype1, contact), (rtype2, orga)],
                         field.clean(self.build_data((rtype1.pk, contact),
                                                     (rtype2.pk, orga),
                                                    )
                                    )
                        )

    def test_clean_with_permission02(self):
        "Perm checking KO"
        user = self.login_as_basic_user()
        contact = self.create_contact()
        orga    = self.create_orga(user=self.other_user)

        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        field = MultiRelationEntityField(required=True, allowed_rtypes=[rtype1.id,rtype2.id])
        field.user = user

        with self.assertRaises(ValidationError) as cm:
            field.clean(self.build_data((rtype1.id, contact),
                                        (rtype2.id, orga),
                                       )
                       )

        exception = cm.exception
        self.assertEqual('linknotallowed', exception.code)
        self.assertEqual(_(u'Some entities are not linkable: {}').format(
                                _(u'Entity #{id} (not viewable)').format(id=orga.id)
                            ),
                         exception.message
                        )

    def test_format_object(self):
        self.login()
        contact = self.create_contact()
        orga    = self.create_orga()
        rtype1 = self.create_loves_rtype()[0]
        rtype2 = self.create_hates_rtype()[0]

        field = MultiRelationEntityField(allowed_rtypes=[rtype1.id, rtype2.id])

        # TODO: assertJSONEqual ?
        with self.assertNoException():
            json_data = json_load(field.from_python([(rtype1, contact), (rtype2, orga)]))

        self.assertEqual([{'entity': contact.id, 'ctype': contact.entity_type_id, 'rtype': rtype1.id},
                          {'entity': orga.id,    'ctype': orga.entity_type_id,    'rtype': rtype2.id},
                         ],
                         json_data
                        )

    def test_autocomplete_property(self):
        field = MultiRelationEntityField()
        self.assertFalse(field.autocomplete)

        field = MultiRelationEntityField(autocomplete=True)
        self.assertTrue(field.autocomplete)

        field.autocomplete = False
        self.assertFalse(field.autocomplete)


class CreatorEntityFieldTestCase(_JSONFieldBaseTestCase):
    def test_void01(self):
        "Model is None"
        with self.assertNumQueries(0):
            field = CreatorEntityField(required=False)

        self.assertIsNone(field.model)
        self.assertIsNone(field.widget.model)
        self.assertIsNone(field.clean('1'))

    def test_void02(self):
        "Model is None ; required"
        with self.assertNumQueries(0):
            field = CreatorEntityField()

        self.assertFieldValidationError(CreatorEntityField, 'required', field.clean, '1')

    def test_format_object(self):
        self.login()
        contact = self.create_contact()
        from_python = CreatorEntityField(FakeContact).from_python
        jsonified = str(contact.pk)
        self.assertEqual(jsonified, from_python(jsonified))
        self.assertEqual(jsonified, from_python(contact))
        self.assertEqual(jsonified, from_python(contact.pk))

    def test_model(self):
        field = CreatorEntityField(FakeContact)
        self.assertEqual(FakeContact, field.model)
        self.assertEqual(FakeContact, field.widget.model)

        field = CreatorEntityField()
        field.model = FakeContact
        self.assertEqual(FakeContact, field.model)
        self.assertEqual(FakeContact, field.widget.model)

    def test_qfilter01(self):
        "Dict"
        self.login()
        contact = self.create_contact()
        qfilter = {'~pk': contact.pk}
        action_url = '/persons/quickforms/from_widget/{}/'.format(contact.entity_type_id)

        field = CreatorEntityField(FakeContact)
        self.assertIsNone(field.q_filter)
        self.assertIsNone(field.q_filter_query)
        self.assertNotEqual(field.create_action_url, action_url)

        # Set qfilter
        field.q_filter = qfilter
        self.assertEqual(field.q_filter, qfilter)
        self.assertIsNotNone(field.q_filter_query)
        self.assertNotEqual(field.create_action_url, action_url)

        # Set creation url
        field.create_action_url = action_url
        self.assertEqual(field.q_filter, qfilter)
        self.assertIsNotNone(field.q_filter_query)
        self.assertEqual(field.create_action_url, action_url)

        # Set both qfilter and creation url in constructor
        field = CreatorEntityField(FakeContact, q_filter=qfilter, create_action_url=action_url)
        self.assertEqual(field.q_filter, qfilter)
        self.assertIsNotNone(field.q_filter_query)
        self.assertEqual(field.create_action_url, action_url)

    def test_qfilter02(self):
        "Dict"
        self.login()
        orga = self.create_orga()
        qfilter = ~Q(id=orga.id)

        field = CreatorEntityField(FakeOrganisation)
        self.assertIsNone(field.q_filter)
        self.assertIsNone(field.q_filter_query)

        # Set qfilter
        field.q_filter = qfilter
        self.assertEqual(field.q_filter, qfilter)
        # self.assertIsNotNone(field.q_filter_query)  # TODO

        # Set both qfilter in constructor
        field = CreatorEntityField(FakeContact, q_filter=qfilter)
        self.assertEqual(field.q_filter, qfilter)

    def test_format_object_with_qfilter01(self):
        "qfilter is a dict"
        self.login()
        contact = self.create_contact()
        field = CreatorEntityField(FakeContact, q_filter={'~pk': contact.pk})

        jsonified = str(contact.pk)
        self.assertEqual(jsonified, field.from_python(jsonified))
        self.assertEqual(jsonified, field.from_python(contact))

        with self.assertRaises(ValueError) as error:
            field.from_python(contact.pk)

        # self.assertIn(str(error.exception),
        #               ('No such entity with id={}.'.format(contact.id),
        #                'No such entity with id={}L.'.format(contact.id),
        #               )
        #              )
        self.assertEqual(str(error.exception),
                         'No such entity with id={}.'.format(contact.id)
                        )

    def test_format_object_with_qfilter02(self):
        "qfilter is a callable returning a dict"
        self.login()
        contact = self.create_contact()
        field = CreatorEntityField(FakeContact, q_filter=lambda: {'~pk': contact.pk})

        jsonified = str(contact.pk)
        self.assertEqual(jsonified, field.from_python(jsonified))
        self.assertEqual(jsonified, field.from_python(contact))

        with self.assertRaises(ValueError) as error:
            field.from_python(contact.pk)

        # self.assertIn(str(error.exception),
        #               ('No such entity with id={}.'.format(contact.id),
        #                'No such entity with id={}L.'.format(contact.id),
        #               )
        #              )
        self.assertEqual(str(error.exception),
                         'No such entity with id={}.'.format(contact.id)
                        )

    def test_format_object_with_qfilter03(self):
        "qfilter is Q"
        self.login()
        contact = self.create_contact()
        field = CreatorEntityField(FakeContact, q_filter=~Q(pk=contact.id))

        jsonified = str(contact.pk)
        self.assertEqual(jsonified, field.from_python(jsonified))
        self.assertEqual(jsonified, field.from_python(contact))

        with self.assertRaises(ValueError) as error:
            field.from_python(contact.id)

        # self.assertIn(str(error.exception),
        #               ('No such entity with id={}.'.format(contact.id),
        #                'No such entity with id={}L.'.format(contact.id),
        #               )
        #              )
        self.assertEqual(str(error.exception),
                         'No such entity with id={}.'.format(contact.id)
                        )

    def test_format_object_from_other_model(self):
        self.login()
        contact = self.create_contact()
        orga = self.create_orga()
        field = CreatorEntityField(FakeContact)

        jsonified = str(contact.pk)
        self.assertEqual(jsonified, field.from_python(jsonified))
        self.assertEqual(jsonified, field.from_python(contact))

        with self.assertRaises(ValueError) as error:
            field.from_python(orga.pk)

        # self.assertIn(str(error.exception),
        #               ('No such entity with id={}.'.format(orga.id),
        #                'No such entity with id={}L.'.format(orga.id),
        #               )
        #              )
        self.assertEqual(str(error.exception),
                         'No such entity with id={}.'.format(orga.id)
                        )

    def test_invalid_qfilter(self):
        self.login()
        contact = self.create_contact()
        action_url = '/persons/quickforms/from_widget/{}/'.format(contact.entity_type_id)

        field = CreatorEntityField(FakeContact)
        # Do this hack for MySql database that uses longs and alter JSON format result
        # qfilter_errors = {
        #     "Invalid type for q_filter (needs dict or Q): ['~pk', {}]".format(contact.id),
        #     "Invalid type for q_filter (needs dict or Q): ['~pk', {}L]".format(contact.id),
        # }

        # Set qfilter property
        field.q_filter = ['~pk', contact.pk]

        with self.assertRaises(ValueError) as error:
            field.q_filter_query()

        # self.assertIn(str(error.exception), qfilter_errors)
        qfilter_error = "Invalid type for q_filter (needs dict or Q): ['~pk', {}]".format(contact.id)
        self.assertEqual(str(error.exception), qfilter_error)

        # Set qfilter in constructor
        field = CreatorEntityField(FakeContact, q_filter=['~pk', contact.pk], create_action_url=action_url)

        with self.assertRaises(ValueError) as error:
            field.q_filter_query()

        # self.assertIn(str(error.exception), qfilter_errors)
        self.assertEqual(str(error.exception), qfilter_error)

    def test_action_buttons_no_custom_quickform(self):
        self.assertIsNotNone(quickforms_registry.get_form(FakeContact))

        user = self.login()
        self.assertTrue(user.has_perm_to_create(FakeContact))

        field = CreatorEntityField(FakeContact, required=False)
        field.user = user

        url = field.create_action_url
        self.assertTrue(url)
        self.assertEqual(url, field.widget.creation_url)

        contact = self.create_contact()
        q_filter = {'~pk': contact.pk}
        field.q_filter = q_filter
        self.assertEqual(q_filter, field.q_filter)
        self.assertEqual(q_filter, field.widget.q_filter)
        self.assertFalse(field.force_creation)
        self.assertEqual('', field.widget.creation_url)

        field.force_creation = True
        self.assertTrue(field.widget.creation_url)

        field = CreatorEntityField(FakeContact, q_filter={'~pk': contact.pk}, required=False)
        field.user = user
        self.assertEqual('', field.widget.creation_url)

    def test_action_buttons_no_user(self):
        self.login()
        field = CreatorEntityField(FakeContact, required=False)
        self.assertIsNone(field.user)

        widget = field.widget
        self.assertEqual('', widget.creation_url)
        self.assertFalse(widget.creation_allowed)

    def test_action_buttons_required(self):
        self.login()
        field = CreatorEntityField(FakeContact)

        self.assertIsNone(field.user)
        self.assertTrue(field.required)
        self.assertEqual(field.widget.actions, [])

    def test_action_buttons_no_quickform(self):
        user = self.login()

        field = CreatorEntityField(CremeEntity, required=False)
        field.user = user

        self.assertTrue(field.user.has_perm_to_create(CremeEntity))
        self.assertIsNone(quickforms_registry.get_form(CremeEntity))
        self.assertFalse(field.widget.creation_url)

    def test_action_buttons_not_allowed(self):
        self.login()

        field = CreatorEntityField(FakeContact, required=False)
        field.user = self.other_user

        self.assertFalse(field.user.has_perm_to_create(FakeContact))
        self.assertIsNotNone(quickforms_registry.get_form(FakeContact))

        widget = field.widget
        self.assertTrue(widget.creation_url)
        self.assertFalse(widget.creation_allowed)

    def test_action_buttons_allowed(self):
        self.assertIsNotNone(quickforms_registry.get_form(FakeContact))

        user = self.login()
        self.assertTrue(user.has_perm_to_create(FakeContact))

        field = CreatorEntityField(FakeContact, required=False)
        self.assertEqual('', field.widget.creation_url)

        field.user = user

        widget = field.widget
        self.assertEqual(widget.creation_url, field.create_action_url)
        self.assertTrue(widget.creation_allowed)

    def test_create_action_url(self):
        self.login()

        field = CreatorEntityField(FakeContact)
        self.assertEqual(reverse('creme_core__quick_form', args=(ContentType.objects.get_for_model(FakeContact).pk,)),
                         field.create_action_url
                        )

        field.create_action_url = url = '/persons/quickforms/from_widget/contact/add/'
        self.assertEqual(url, field.create_action_url)

    def test_clean_empty_required(self):
        clean = CreatorEntityField(FakeContact, required=True).clean
        self.assertFieldValidationError(CreatorEntityField, 'required', clean, None)
        self.assertFieldValidationError(CreatorEntityField, 'required', clean, '')

    def test_clean_empty_not_required(self):
        with self.assertNoException():
            value = CreatorEntityField(FakeContact, required=False).clean(None)

        self.assertIsNone(value)

    def test_clean_invalid_json(self):
        clean = CreatorEntityField(FakeContact, required=False).clean
        self.assertFieldValidationError(CreatorEntityField, 'invalidformat', clean, '{12')

    def test_clean_invalid_data_type(self):
        clean = CreatorEntityField(FakeContact, required=False).clean
        self.assertFieldValidationError(CreatorEntityField, 'invalidtype', clean, '[]')
        self.assertFieldValidationError(CreatorEntityField, 'invalidtype', clean, "{}")

    def test_clean_unknown_entity(self):
        self.login()
        contact = self.create_contact()
        orga = self.create_orga()

        self.assertFieldValidationError(CreatorEntityField, 'doesnotexist',
                                        CreatorEntityField(model=FakeContact).clean,
                                        str(orga.pk)
                                       )
        self.assertFieldValidationError(CreatorEntityField, 'doesnotexist',
                                        CreatorEntityField(model=FakeOrganisation).clean,
                                        str(contact.pk)
                                       )

    def test_clean_with_permission01(self):
        "Perm checking OK"
        user = self.login_as_basic_user()

        orga = self.create_orga()

        field = CreatorEntityField(model=FakeOrganisation)
        field.user = user
        self.assertEqual(orga, field.clean(str(orga.pk)))

    def test_clean_with_permission02(self):
        "Perm checking KO"
        user = self.login_as_basic_user()

        orga = self.create_orga(user=self.other_user)

        field = CreatorEntityField(model=FakeOrganisation)
        field.user = user

        with self.assertRaises(ValidationError) as cm:
            field.clean(str(orga.pk))
        self.assertEqual('linknotallowed', cm.exception.code)

    def test_clean_deleted_entity(self):
        self.login()
        self.assertFieldValidationError(CreatorEntityField, 'doesnotexist',
                                        CreatorEntityField(model=FakeContact).clean,
                                        str(self.create_contact(is_deleted=True).pk)
                                       )

    def test_clean_filtered_entity01(self):
        "qfilter is a dict"
        user = self.login()
        contact = self.create_contact()

        with self.assertNumQueries(0):
            field = CreatorEntityField(FakeContact)

        field.user = user
        field.q_filter = {'~pk': contact.pk}
        self.assertFieldValidationError(CreatorEntityField, 'doesnotexist', field.clean, str(contact.pk))

        field.q_filter = {'pk': contact.pk}
        self.assertEqual(contact, field.clean(str(contact.pk)))

    def test_clean_filtered_entity02(self):
        "qfilter is a Q"
        user = self.login()
        orga = self.create_orga()

        with self.assertNumQueries(0):
            field = CreatorEntityField(FakeOrganisation)

        field.user = user
        field.q_filter = ~Q(name__startswith=orga.name)
        self.assertFieldValidationError(CreatorEntityField, 'doesnotexist', field.clean, str(orga.pk))

        field.q_filter = Q(name__startswith=orga.name)
        self.assertEqual(orga, field.clean(str(orga.pk)))

    def test_hook(self):
        user = self.login()

        form = fake_forms.FakeContactForm(user=user)

        with self.assertNoException():
            image_f = form.fields['image']

        self.assertIsInstance(image_f, CreatorEntityField)
        self.assertEqual(_(u'Photograph'), image_f.label)
        self.assertFalse(image_f.required)
        self.assertFalse(image_f.q_filter)

        # -----
        form = fake_forms.FakeOrganisationForm(user=user)

        with self.assertNoException():
            image_f = form.fields['image']

        self.assertIsInstance(image_f, CreatorEntityField)
        self.assertEqual(_(u'Logo'), image_f.label)
        self.assertTrue(callable(image_f.q_filter))
        self.assertQEqual(Q(user__is_staff=False), image_f.q_filter_query)


class MultiCreatorEntityFieldTestCase(_JSONFieldBaseTestCase):
    def test_void01(self):
        "Model is None"
        user = self.login()

        with self.assertNumQueries(0):
            field = MultiCreatorEntityField(required=False, user=user)

        self.assertEqual([], field.clean('[1]'))

    def test_void02(self):
        "Model is None ; required"
        with self.assertNumQueries(0):
            field = MultiCreatorEntityField()

        self.assertFieldValidationError(MultiCreatorEntityField, 'required',
                                        field.clean, '[1]',
                                       )

    def test_format_object(self):
        self.login()
        contact = self.create_contact()

        field = MultiCreatorEntityField(FakeContact)
        self.assertEqual(field.value_type, list)

        from_python = field.from_python
        jsonified = '[{}]'.format(contact.id)
        self.assertEqual(jsonified, from_python(jsonified))
        self.assertEqual(jsonified, from_python([contact]))
        self.assertEqual(jsonified, from_python([contact.pk]))
        self.assertEqual('', from_python([]))

    def test_format_object_list(self):
        self.login()

        contact = self.create_contact()
        contact2 = self.create_contact()
        contact3 = self.create_contact()

        field = MultiCreatorEntityField(FakeContact)
        self.assertEqual(field.value_type, list)

        from_python = field.from_python
        jsonified = json_dump([contact.id, contact2.id, contact3.id])
        self.assertEqual(jsonified, from_python(jsonified))
        self.assertEqual(jsonified, from_python([contact, contact2, contact3]))
        self.assertEqual(jsonified, from_python([contact.pk, contact2.pk, contact3.pk]))

    def test_qfilter(self):
        self.login()
        contact = self.create_contact()
        qfilter = {'~pk': contact.pk}
        # action_url = '/persons/quickforms/from_widget/%s/1' % contact.entity_type_id
        action_url = '/persons/quickforms/from_widget/{}/'.format(contact.entity_type_id)

        field = MultiCreatorEntityField(FakeContact)
        self.assertIsNone(field.q_filter)

        field.q_filter = qfilter
        self.assertIsNotNone(field.q_filter)

        field = MultiCreatorEntityField(FakeContact, q_filter=qfilter, create_action_url=action_url)
        self.assertIsNotNone(field.q_filter)
        self.assertEqual(field.create_action_url, action_url)

    def test_format_object_with_qfilter(self):
        self.login()

        contact1 = self.create_contact()
        contact2 = self.create_contact()
        contact3 = self.create_contact()

        field = MultiCreatorEntityField(FakeContact, q_filter={'~pk': contact1.id})

        jsonified = json_dump([contact1.id, contact2.id, contact3.id])
        self.assertEqual(jsonified, field.from_python(jsonified))
        self.assertEqual(jsonified, field.from_python([contact1, contact2, contact3]))
        self.assertEqual('[{}, {}]'.format(contact2.id, contact3.id),
                         field.from_python([contact2.pk, contact3.pk])
                        )

        with self.assertRaises(ValueError) as error:
            field.from_python([contact1.pk, contact2.pk, contact3.pk])

        ids = [str(e.id) for e in (contact1, contact2, contact3)]
        # self.assertIn(str(error.exception),
        #               ("The entities with ids [{}] don't exist.".format(', '.join(ids)),
        #                "The entities with ids [{}] don't exist.".format('L, '.join(ids)),
        #               )
        #              )
        self.assertEqual(str(error.exception),
                         "The entities with ids [{}] don't exist.".format(', '.join(ids)),
                        )

    def test_format_object_from_other_model(self):
        self.login()

        contact = self.create_contact()
        contact2 = self.create_contact()
        orga = self.create_orga()

        field = MultiCreatorEntityField(FakeContact)

        jsonified = json_dump([orga.id, contact.id, contact2.id])

        self.assertEqual(jsonified, field.from_python(jsonified))
        self.assertEqual(jsonified, field.from_python([orga, contact, contact2]))

        with self.assertRaises(ValueError) as error:
            field.from_python([orga.pk, contact.pk, contact2.pk])

        ids = [str(e.id) for e in [orga, contact, contact2]]
        # self.assertIn(str(error.exception),
        #               ("The entities with ids [{}] don't exist.".format(', '.join(ids)),
        #                "The entities with ids [{}] don't exist.".format('L, '.join(ids)),
        #               )
        #              )
        self.assertEqual(str(error.exception),
                         "The entities with ids [{}] don't exist.".format(', '.join(ids)),
                        )

    def test_invalid_qfilter(self):
        self.login()
        contact = self.create_contact()
        action_url = '/persons/quickforms/from_widget/{}/'.format(contact.entity_type_id)

        field = MultiCreatorEntityField(FakeContact)
        # # Do this hack for MySql database that uses longs and alter json format result
        # qfilter_errors = ("Invalid type for q_filter (needs dict or Q): ['~pk', {}]".format(contact.id),
        #                   "Invalid type for q_filter (needs dict or Q): ['~pk', {}L]".format(contact.id),
        #                  )

        field.q_filter = ['~pk', contact.pk]

        with self.assertRaises(ValueError) as error:
            field.q_filter_query

        # self.assertIn(str(error.exception), qfilter_error)
        qfilter_error = "Invalid type for q_filter (needs dict or Q): ['~pk', {}]".format(contact.id)
        self.assertEqual(str(error.exception), qfilter_error)

        field = MultiCreatorEntityField(FakeContact, q_filter=['~pk', contact.pk], create_action_url=action_url)

        with self.assertRaises(ValueError) as error:
            field.q_filter_query

        # self.assertIn(str(error.exception), qfilter_errors)
        self.assertEqual(str(error.exception), qfilter_error)

    def test_create_action_url(self):
        self.login()

        field = MultiCreatorEntityField(FakeContact)
        self.assertEqual(reverse('creme_core__quick_form', args=(ContentType.objects.get_for_model(FakeContact).pk,)),
                         field.create_action_url
                        )

        field.create_action_url = url = '/persons/quickforms/from_widget/contact/add/'
        self.assertEqual(url, field.create_action_url)

    def test_clean_empty_required(self):
        clean = MultiCreatorEntityField(FakeContact, required=True).clean
        self.assertFieldValidationError(MultiCreatorEntityField, 'required', clean, None)
        self.assertFieldValidationError(MultiCreatorEntityField, 'required', clean, '')
        self.assertFieldValidationError(MultiCreatorEntityField, 'required', clean, '[]')

    def test_clean_empty_not_required(self):
        with self.assertNoException():
            value = MultiCreatorEntityField(FakeContact, required=False).clean(None)

        self.assertEqual(value, [])

        with self.assertNoException():
            value = MultiCreatorEntityField(FakeContact, required=False).clean("[]")

        self.assertEqual(value, [])

    def test_clean_invalid_json(self):
        field = MultiCreatorEntityField(FakeContact, required=False)
        self.assertFieldValidationError(MultiCreatorEntityField, 'invalidformat', field.clean, '{12')
        self.assertFieldValidationError(MultiCreatorEntityField, 'invalidformat', field.clean, '[12')

    def test_clean_invalid_data_type(self):
        user = self.login()

        clean = MultiCreatorEntityField(FakeContact, required=False, user=user).clean
        self.assertFieldValidationError(MultiCreatorEntityField, 'invalidtype', clean, '""')
        self.assertFieldValidationError(MultiCreatorEntityField, 'invalidtype', clean, "{}")
        self.assertFieldValidationError(MultiCreatorEntityField, 'invalidtype', clean, "[{}]")

    def test_clean_unknown_entity(self):
        self.login()
        contact = self.create_contact()
        orga = self.create_orga()

        self.assertFieldValidationError(MultiCreatorEntityField, 'doesnotexist',
                                        MultiCreatorEntityField(model=FakeContact).clean,
                                        '[{}]'.format(orga.id)
                                       )
        self.assertFieldValidationError(MultiCreatorEntityField, 'doesnotexist',
                                        MultiCreatorEntityField(model=FakeOrganisation).clean,
                                        '[{}]'.format(contact.id)
                                       )

    def test_clean_deleted_entity(self):
        self.login()
        self.assertFieldValidationError(MultiCreatorEntityField, 'doesnotexist',
                                        MultiCreatorEntityField(model=FakeContact).clean,
                                        '[{}]'.format(self.create_contact(is_deleted=True).id)
                                       )

    def test_clean_entities(self):
        user = self.login()
        contact = self.create_contact()
        contact2 = self.create_contact()

        field = MultiCreatorEntityField(FakeContact)
        field.user = user
        self.assertEqual([contact, contact2],
                         field.clean(json_dump([contact.id, contact2.id]))
                        )

    def test_clean_filtered_entities(self):
        user = self.login()
        contact = self.create_contact()

        with self.assertNumQueries(0):
            field = MultiCreatorEntityField(FakeContact)
            field.q_filter = {'~pk': contact.pk}

        field.user = user
        self.assertFieldValidationError(MultiCreatorEntityField, 'doesnotexist',
                                        field.clean, '[{}]'.format(contact.id),
                                       )

        field.q_filter = {'pk': contact.pk}
        self.assertEqual([contact], field.clean('[{}]'.format(contact.id)))

    def test_clean_with_permission01(self):
        "Perm checking OK"
        user = self.login_as_basic_user()

        orga1 = self.create_orga('Orga #1')
        orga2 = self.create_orga('Orga #2')

        field = MultiCreatorEntityField(model=FakeOrganisation)
        field.user = user
        self.assertEqual([orga1, orga2], field.clean(json_dump([orga1.id, orga2.id])))

    def test_clean_with_permission02(self):
        "Perm checking KO"
        user = self.login_as_basic_user()

        orga1 = self.create_orga('Orga #1')
        orga2 = self.create_orga('Orga #2', user=self.other_user)

        field = MultiCreatorEntityField(model=FakeOrganisation, user=user)

        with self.assertRaises(ValidationError) as cm:
            field.clean('[{}, {}]'.format(orga1.id, orga2.id))
        self.assertEqual('linknotallowed', cm.exception.code)

    def test_hook(self):
        user = self.login()

        form = fake_forms.FakeEmailCampaignForm(user=user)

        with self.assertNoException():
            mlists_f = form.fields['mailing_lists']

        self.assertIsInstance(mlists_f, MultiCreatorEntityField)
        self.assertEqual(_(u'Related mailing lists'), mlists_f.label)
        self.assertFalse(mlists_f.required)
        self.assertFalse(mlists_f.q_filter)

        # -----
        form = fake_forms.FakeProductForm(user=user)

        with self.assertNoException():
            images_f = form.fields['images']

        self.assertIsInstance(images_f, CreatorEntityField)
        self.assertEqual(_(u'Images'), images_f.label)
        self.assertEqual({'user__is_active': True}, images_f.q_filter)


class FilteredEntityTypeFieldTestCase(_JSONFieldBaseTestCase):
    @staticmethod
    def build_value(ctype_id, efilter_id):
        return json_dump({'ctype': str(ctype_id), 'efilter': efilter_id})

    @classmethod
    def setUpClass(cls):
        # super(FilteredEntityTypeFieldTestCase, cls).setUpClass()
        super().setUpClass()

        get_ct = ContentType.objects.get_for_model
        cls.ct_contact = get_ct(FakeContact)
        cls.ct_orga    = get_ct(FakeOrganisation)

    def setUp(self):
        # super(FilteredEntityTypeFieldTestCase, self).setUp()
        super().setUp()
        self.login()

    def test_clean_empty_required(self):
        clean = FilteredEntityTypeField(required=True).clean
        self.assertFieldValidationError(FilteredEntityTypeField, 'required', clean, None)
        self.assertFieldValidationError(FilteredEntityTypeField, 'required', clean, '')

    def test_clean_invalid_json(self):
        field = FilteredEntityTypeField(required=False)
        self.assertFieldValidationError(FilteredEntityTypeField, 'invalidformat', field.clean,
                                        '{"ctype":"10", "efilter":"creme_core-testfilter"'
                                       )

    def test_clean_invalid_data_type(self):
        clean = FilteredEntityTypeField(required=False).clean
        self.assertFieldValidationError(FilteredEntityTypeField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(FilteredEntityTypeField, 'invalidtype', clean, '"{}"')
        self.assertFieldValidationError(FilteredEntityTypeField, 'invalidformat', clean, '{"ctype":"not_an_int", "efilter":"creme_core-testfilter"}')

    def test_clean_required_ctype(self):
        self.assertFieldValidationError(FilteredEntityTypeField, 'ctyperequired',
                                        FilteredEntityTypeField(required=True).clean,
                                        self.build_value('', '')
                                       )

    def test_clean_unknown_ctype(self):
        self.assertFieldValidationError(FilteredEntityTypeField, 'ctypenotallowed',
                                        FilteredEntityTypeField().clean,
                                        self.build_value(1024, '')
                                       )

    def test_clean_forbidden_ctype01(self):
        "Allowed ContentTypes given as a list of ContentType instances"
        ctypes = [self.ct_contact]
        error_msg = self.build_value(self.ct_orga.id, '')

        field = FilteredEntityTypeField(ctypes=ctypes)
        self.assertEqual(ctypes, field.ctypes)

        self.assertFieldValidationError(FilteredEntityTypeField, 'ctypenotallowed',
                                        field.clean, error_msg
                                       )

        # Use setter
        field = FilteredEntityTypeField()
        field.ctypes = ctypes
        self.assertFieldValidationError(FilteredEntityTypeField, 'ctypenotallowed',
                                        field.clean, error_msg
                                       )

    def test_clean_forbidden_ctype02(self):
        "Allowed ContentTypes given as a list of ID"
        ctypes = [self.ct_contact.id]
        error_msg = self.build_value(str(self.ct_orga.id), '')

        self.assertFieldValidationError(FilteredEntityTypeField, 'ctypenotallowed',
                                        FilteredEntityTypeField(ctypes=ctypes).clean,
                                        error_msg
                                       )

        # Use setter
        field = FilteredEntityTypeField()
        field.ctypes = ctypes
        self.assertFieldValidationError(FilteredEntityTypeField, 'ctypenotallowed',
                                        field.clean, error_msg
                                       )

    def test_clean_forbidden_ctype03(self):
        "Allowed ContentTypes given as a list of ID & instances"
        ctypes = [self.ct_contact.id, self.ct_orga]

        self.assertFieldValidationError(FilteredEntityTypeField, 'ctypenotallowed',
                                        FilteredEntityTypeField(ctypes=ctypes).clean,
                                        self.build_value(ContentType.objects.get_for_model(FakeImage).id, '')
                                       )

    def test_clean_unknown_efilter01(self):
        "EntityFilter does not exist"
        self.assertFieldValidationError(FilteredEntityTypeField, 'invalidefilter',
                                        FilteredEntityTypeField(user=self.user).clean,
                                        self.build_value(self.ct_contact.id, 'idonotexist')
                                       )

    def test_clean_unknown_efilter02(self):
        "Content type does not correspond to EntityFilter"
        efilter = EntityFilter.create('test-filter01', 'Acme', FakeOrganisation, is_custom=True)
        self.assertFieldValidationError(FilteredEntityTypeField, 'invalidefilter',
                                        FilteredEntityTypeField(user=self.user).clean,
                                        self.build_value(self.ct_contact.id, efilter.id)
                                       )

    def test_clean_private_filter(self):
        "Private invisible filter -> no user"
        efilter = EntityFilter.create('test-filter01', 'John', FakeContact, is_custom=True,
                                      user=self.other_user, is_private=True,
                                     )
        field = FilteredEntityTypeField()
        field.user = self.user
        self.assertFieldValidationError(FilteredEntityTypeField, 'invalidefilter',
                                        field.clean,
                                        self.build_value(self.ct_contact.id, efilter.id)
                                       )

    def test_clean_void(self):
        field = FilteredEntityTypeField(required=False)
        field.user = self.user

        self.assertEqual((None, None), field.clean(self.build_value('', '')))
        self.assertEqual((None, None), field.clean('{"ctype": "0", "efilter": null}'))

    def test_clean_only_ctype01(self):
        "All element of this ContentType are allowed"
        field = FilteredEntityTypeField()
        field.user = self.user

        self.assertEqual((self.ct_contact, None),
                         field.clean(self.build_value(self.ct_contact.id, ''))
                        )

    def test_clean_only_ctype02(self):
        "Allowed ContentTypes given as a sequence of instance/id"
        ct_contact = self.ct_contact
        ct_orga    = self.ct_orga

        field = FilteredEntityTypeField([ct_contact, ct_orga.id])
        field.user = self.user

        self.assertEqual((ct_contact, None),
                         field.clean(self.build_value(ct_contact.id, ''))
                        )
        self.assertEqual((ct_orga, None),
                         field.clean(self.build_value(ct_orga.id, ''))
                        )

    def test_clean_with_filter01(self):
        efilter = EntityFilter.create('test-filter01', 'John', FakeContact, is_custom=True)

        field = FilteredEntityTypeField()
        field.user = self.user

        ct = self.ct_contact
        self.assertEqual((ct, efilter),
                         field.clean(self.build_value(ct.id, efilter.id))
                        )

    def test_clean_with_filter02(self):
        "Private visible filter"
        user = self.user
        efilter = EntityFilter.create('test-filter01', 'John', FakeContact, is_custom=True,
                                      user=user, is_private=True,
                                     )
        field = FilteredEntityTypeField()
        field.user = user
        ct = self.ct_contact
        self.assertEqual((ct, efilter),
                         field.clean(self.build_value(ct.id, efilter.id))
                        )
