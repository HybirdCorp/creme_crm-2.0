# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import re

from logging import debug

from django.utils.safestring import mark_safe
from django.forms import CharField, BooleanField, ModelChoiceField, ValidationError
from django.forms.widgets import HiddenInput, CheckboxInput, PasswordInput
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from creme_core.models import Relation, RelationType, CremeProfile, CremeRole
from creme_core.forms import CremeForm, CremeModelForm
from creme_core.forms.fields import CremeEntityField
from creme_core.forms.widgets import ListViewWidget

from persons.models import Contact, Organisation


_get_ct = ContentType.objects.get_for_model

class UserAddForm(CremeModelForm):
    password_1     = CharField(label=_(u"Password"), min_length=6, widget=PasswordInput(), required=True)
    password_2     = CharField(label=_(u"Confirm password"), min_length=6, widget=PasswordInput(), required=True)
    role           = ModelChoiceField(label=_(u"Role"), queryset=CremeRole.objects.all())
    contact_exists = BooleanField(label=_(u"His related contact already exists ?"), required=False,
                                  help_text=_(u"Uncheck if you want the related contact to be automatically created."),
                                  widget=CheckboxInput(attrs={'onclick': 'config.handleShowContacts(this, "id_contact_div");'}))
    contact        = CremeEntityField(label=_(u"Contacts"), model=Contact, q_filter={'is_user': None},
                                      widget=ListViewWidget(attrs={'style':'display:none;'}), required=False)

    organisation   = ModelChoiceField(label=_(u"User organisation"), queryset=Organisation.get_all_managed_by_creme())
    relation       = ModelChoiceField(label=_(u"Position in the organisation"),
                                      queryset=RelationType.objects.filter(subject_ctypes=_get_ct(Contact), object_ctypes=_get_ct(Organisation)))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_superuser')

    def clean_username(self):
        username = self.data['username']
        if not re.match("^(\w)[\w-]*$", username):
            raise ValidationError(ugettext(u"The username must only contain alphanumeric (a-z, A-Z, 0-9), "
                                            "hyphen and underscores are allowed (but not as first character)."))
        return username

    def clean_password_2(self):
        data = self.data
        pw2  = data['password_2']

        if data['password_1'] != pw2:
            raise ValidationError(ugettext(u"Passwords are different"))

        return pw2

    def clean_contact(self):
        get_data = self.cleaned_data.get
        contact_exists = get_data('contact_exists', False)
        contact = get_data('contact', None)

        if contact_exists:
            self.fields['contact'].widget.attrs['style'] = "display:block;"

            if not contact:
                raise ValidationError(ugettext(u"Select a Contact if he already exists"))

        return contact

    def save(self):
        cleaned  = self.cleaned_data
        instance = self.instance

        instance.set_password(cleaned['password_1'])
        super(UserAddForm, self).save()

        CremeProfile.objects.create(creme_role=cleaned['role'], user=instance)

        contact = cleaned.get('contact', None)

        if not contact:
            contact = Contact()
            contact.last_name  = instance.last_name or instance.username
            contact.first_name = instance.first_name or instance.username
            contact.user = instance

        contact.is_user = instance
        contact.save()

        Relation.create(contact, cleaned['relation'].id, cleaned['organisation'])

        return instance


class UserEditForm(CremeModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'is_superuser')


class UserChangePwForm(CremeForm):
    password_1 = CharField(label=_(u"Password"), min_length=6, widget=PasswordInput())
    password_2 = CharField(label=_(u"Confirm password"), min_length=6, widget=PasswordInput())

    def clean_password_2(self):
        data = self.data
        pw2  = data['password_2']

        if data['password_1'] != pw2:
            raise ValidationError(ugettext(u"Passwords are different"))

        return pw2

    def save(self):
        user = self.initial.get('user')
        pw   = self.cleaned_data.get('password_1')

        if user and pw:
            user.set_password(pw)
            user.save()
