# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2019  Hybird
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

from datetime import datetime, time, timedelta
from functools import partial
import logging

from django.apps import apps
from django.contrib.auth import get_user_model
from django.forms import ModelChoiceField, ModelMultipleChoiceField, DateTimeField, TimeField, ValidationError
from django.utils.timezone import localtime
from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.forms import (validators, CremeEntityForm,
    MultiCreatorEntityField, MultiGenericEntityField, DatePeriodField)
from creme.creme_core.forms.widgets import CalendarWidget
from creme.creme_core.models import RelationType, Relation, SettingValue
from creme.creme_core.utils.dates import make_aware_dt

from creme.persons import get_contact_model

from .. import get_activity_model, constants
from ..models import ActivityType, Calendar, ActivitySubType
from ..utils import check_activity_collisions
from ..setting_keys import form_user_messages_key
from .activity_type import ActivityTypeField
from .fields import UserParticipationField

logger = logging.getLogger(__name__)
Contact = get_contact_model()
Activity = get_activity_model()


class _ActivityForm(CremeEntityForm):
    type_selector = ActivityTypeField(label=_(u'Type'),
                                      types=ActivityType.objects.exclude(pk=constants.ACTIVITYTYPE_INDISPO),
                                     )

    start_time = TimeField(label=_(u'Start time'), required=False)
    end_time   = TimeField(label=_(u'End time'), required=False)

    error_messages = {
        'floating_cannot_busy': _(u"A floating on the day activity can't busy its participants"),
        'no_start': _(u"You can't set the end of your activity without setting its start"),
        'end_before_start_time': _(u'End time is before start time'),
    }

    class Meta(CremeEntityForm.Meta):
        model = Activity
        exclude = CremeEntityForm.Meta.exclude + ('type', 'sub_type')
        widgets = {'start': CalendarWidget, 'end': CalendarWidget}
        help_texts = {'end': _(u'Default duration of the type will be used if you leave blank.')}

    def __init__(self, *args, **kwargs):
        # super(_ActivityForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.participants = set()  # All Contacts who participate: me, other users, other contacts

        duration_field = self.fields.get('duration')
        if duration_field:
            duration_field.help_text = _('It is only informative '
                                         'and is not used to compute the end time.'
                                        )

    def clean(self):
        # cdata = super(_ActivityForm, self).clean()
        cdata = super().clean()

        if not self._errors:
            self.floating_type = self._clean_interval(self._get_activity_type_n_subtype()[0])

            start = cdata['start']
            if start:
                collisions = check_activity_collisions(start, cdata['end'],
                                                       self._get_participants_2_check(),
                                                       busy=cdata['busy'],
                                                       exclude_activity_id=self.instance.pk,
                                                      )
                if collisions:
                    raise ValidationError(collisions)

        return cdata

    def _clean_interval(self, atype):
        cdata = self.cleaned_data
        start = cdata['start']
        end   = cdata['end']

        if not start and not end:
            return constants.FLOATING

        floating_type = constants.NARROW

        get = cdata.get
        is_all_day = get('is_all_day', False)
        start_time = get('start_time')
        end_time   = get('end_time')

        # TODO: not start, not end, start time, end time => floating activity with time set but lost in the process

        if start_time is None and end_time is None:
            if not is_all_day:
                if get('busy', False):
                    raise ValidationError(self.error_messages['floating_cannot_busy'],
                                          code='floating_cannot_busy',
                                         )

                floating_type = constants.FLOATING_TIME

        if not start and end:
            raise ValidationError(self.error_messages['no_start'], code='no_start')

        if start and start_time:
            start = make_aware_dt(datetime.combine(start, start_time))

        if end and end_time:
            end = make_aware_dt(datetime.combine(end, end_time))

        if start and not end:
            if end_time is not None:
                end = make_aware_dt(datetime.combine(start, end_time))
            else:
                tdelta = atype.as_timedelta()

                if (is_all_day or floating_type == constants.FLOATING_TIME) and tdelta.days:
                    # In 'all day' mode, we round the number of day
                    days = tdelta.days - 1  # Activity already takes 1 day (we do not want it takes 2)

                    if tdelta.seconds:
                        days += 1

                    tdelta = timedelta(days=days)

                end = start + tdelta

        if is_all_day or floating_type == constants.FLOATING_TIME:
            start = make_aware_dt(datetime.combine(start, time(hour=0, minute=0)))
            end   = make_aware_dt(datetime.combine(end, time(hour=23, minute=59)))

        if start > end:
            raise ValidationError(self.error_messages['end_before_start_time'],
                                  code='end_before_start_time',
                                 )

        cdata['start'] = start
        cdata['end'] = end

        return floating_type

    def _get_activity_type_n_subtype(self):
        return self.cleaned_data['type_selector']

    def _get_participants_2_check(self):
        return self.participants

    def save(self, *args, **kwargs):
        instance = self.instance
        instance.floating_type = self.floating_type
        instance.type, instance.sub_type = self._get_activity_type_n_subtype()

        # super(_ActivityForm, self).save(*args, **kwargs)
        super().save(*args, **kwargs)

        # create_relation = partial(Relation.objects.create, object_entity=instance,
        #                           type_id=constants.REL_SUB_PART_2_ACTIVITY, user=instance.user,
        #                          )
        #
        # for participant in self.participants:
        #     create_relation(subject_entity=participant)
        Relation.objects.safe_multi_save(
            Relation(subject_entity=participant,
                     type_id=constants.REL_SUB_PART_2_ACTIVITY,
                     object_entity=instance,
                     user=instance.user,
                    ) for participant in self.participants
        )

        return instance


class ActivityEditForm(_ActivityForm):
    blocks = _ActivityForm.blocks.new(
        ('datetime', _(u'When'), ['is_all_day', 'start', 'start_time', 'end', 'end_time']),
    )

    @staticmethod
    def _localize(dt):
        return localtime(dt) if dt else dt

    def __init__(self, *args, **kwargs):
        # super(ActivityEditForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        fields = self.fields
        instance = self.instance

        type_f = fields['type_selector']
        type_f.initial = (instance.type_id, instance.sub_type_id)

        if self.instance.type_id == constants.ACTIVITYTYPE_INDISPO:
            type_f.types = ActivityType.objects.filter(pk=constants.ACTIVITYTYPE_INDISPO)

        if instance.floating_type == constants.NARROW:
            start = self._localize(instance.start)
            if start:
                fields['start_time'].initial = start.time()

            end = self._localize(instance.end)
            if end:
                fields['end_time'].initial = end.time()

    def _get_participants_2_check(self):
        return self.instance.get_related_entities(constants.REL_OBJ_PART_2_ACTIVITY)


class _ActivityCreateForm(_ActivityForm):
    participating_users = ModelMultipleChoiceField(label=_(u'Other participating users'),
                                                   queryset=get_user_model().objects.filter(is_staff=False),
                                                   required=False,
                                                  )

    # TODO: factorise with ParticipantCreateForm
    def clean_participating_users(self):
        users = set()

        for user in self.cleaned_data['participating_users']:
            if not user.is_team:
                users.add(user)
            else:
                users.update(user.teammates.values())

        self.participants.update(validators.validate_linkable_entities(Contact.objects.filter(is_user__in=users),
                                                                       self.user,
                                                                      )
                                )

        return users

    def save(self, *args, **kwargs):
        # instance = super(_ActivityCreateForm, self).save(*args, **kwargs)
        instance = super().save(*args, **kwargs)

        for part_user in self.cleaned_data['participating_users']:
            # TODO: regroup queries ??
            instance.calendars.add(Calendar.get_user_default_calendar(part_user))

        return instance


class ActivityCreateForm(_ActivityCreateForm):
    my_participation = UserParticipationField(label=_(u'Do I participate to this activity?'), empty_label=None)

    other_participants  = MultiCreatorEntityField(label=_(u'Other participants'), model=Contact, required=False)
    subjects            = MultiGenericEntityField(label=_(u'Subjects'), required=False)
    linked_entities     = MultiGenericEntityField(label=_(u'Entities linked to this activity'), required=False)

    error_messages = dict(
        _ActivityCreateForm.error_messages,
        no_participant=_('No participant'),
        alert_on_floating=_('You cannot set a relative alert on a floating activity'),
    )

    blocks = _ActivityForm.blocks.new(
        ('datetime',       _(u'When'),         ['start', 'start_time', 'end', 'end_time', 'is_all_day']),
        ('participants',   _(u'Participants'), ['my_participation', 'participating_users',
                                                'other_participants', 'subjects', 'linked_entities']),
        ('alert_datetime', _(u'Generate an alert on a specific date'), ['alert_start']),
        ('alert_period',   _(u'Generate an alert in a while'),         ['alert_period']),
        ('informed_users', _(u'Users to keep informed'),               ['informed_users']),
    )

    def __init__(self, activity_type_id=None, *args, **kwargs):
        # super(ActivityCreateForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        user   = self.user
        fields = self.fields

        if activity_type_id:
            # TODO: improve help_text of end (we know the type default duration)
            fields['type_selector'].types = ActivityType.objects.filter(pk=activity_type_id)

        fields['my_participation'].initial = (True, Calendar.get_user_default_calendar(user).id)

        subjects_field = fields['subjects']
        subjects_field.allowed_models = [ct.model_class() 
                                            for ct in RelationType.objects
                                                                  .get(pk=constants.REL_SUB_ACTIVITY_SUBJECT)
                                                                  .subject_ctypes.all()
                                        ]
        if self.instance.is_auto_orga_subject_enabled():
            subjects_field.help_text = _('The organisations of the participants will be automatically added as subjects')

        fields['participating_users'].queryset = get_user_model().objects.filter(is_staff=False) \
                                                                         .exclude(pk=user.id)

        other_f = fields['other_participants']
        other_f.q_filter = {'is_user__isnull': True}
        # The creation view cannot create a Contact with a non-null 'is_user'.
        other_f.force_creation = True  # TODO: in constructor

        if apps.is_installed('creme.assistants'):
            self._add_specified_alert_fields(fields)
            self._add_duration_alert_fields(fields)
            self._add_informed_users_fields(fields)

    @staticmethod
    def _add_specified_alert_fields(fields):
        fields['alert_start'] = DateTimeField(label=_(u'Generate an alert on a specific date'), required=False)

    @staticmethod
    def _add_duration_alert_fields(fields):
        fields['alert_period'] = DatePeriodField(label=_(u'Generate an alert in a while'),
                                                 required=False,
                                                 help_text=_(u"How long before the activity's"
                                                             u" start the alert is raised?"
                                                            ),
                                                 period_names=('minutes', 'hours', 'days', 'weeks'),
                                                )

    @staticmethod
    def _add_informed_users_fields(fields):
        # try:
        #     sv = SettingValue.objects.get(key_id=constants.SETTING_FORM_USERS_MSG)
        # except SettingValue.DoesNotExist:
        #     logger.critical('SettingValue with key=%s cannot be found !'
        #                     ' ("creme_populate" command has not been run correctly)',
        #                     constants.SETTING_FORM_USERS_MSG
        #                    )
        # else:
        #     if sv.value:
        #         fields['informed_users'] = ModelMultipleChoiceField(queryset=get_user_model().objects.filter(is_staff=False),
        #                                                             required=False,
        #                                                             label=_(u'Users to keep informed'),
        #                                                            )
        if SettingValue.objects.get_4_key(form_user_messages_key, default=False).value:
            fields['informed_users'] = ModelMultipleChoiceField(
                queryset=get_user_model().objects.filter(is_staff=False),
                required=False,
                label=_('Users to keep informed'),
            )

    def clean_alert_period(self):
        cdata = self.cleaned_data
        alert_period = cdata['alert_period']

        if alert_period and not cdata.get('start'):
            raise ValidationError(self.error_messages['alert_on_floating'],
                                  code='alert_on_floating',
                                 )

        return alert_period

    def clean_my_participation(self):
        my_participation = self.cleaned_data['my_participation']

        if my_participation[0]:
            user = self.user
            self.participants.add(validators.validate_linkable_entity(user.linked_contact, user))

        return my_participation

    def clean_other_participants(self):
        participants = self.cleaned_data['other_participants']
        self.participants.update(participants)
        return participants

    def clean(self):
        if not self._errors:
            cdata = self.cleaned_data

            if not cdata['my_participation'][0] and not cdata['participating_users']:
                raise ValidationError(self.error_messages['no_participant'], code='no_participant')

        # return super(ActivityCreateForm, self).clean()
        return super().clean()

    def save(self, *args, **kwargs):
        # instance = super(ActivityCreateForm, self).save(*args, **kwargs)
        instance = super().save(*args, **kwargs)

        self._generate_alerts()
        self._generate_user_messages()

        cdata = self.cleaned_data

        i_participate, my_calendar = cdata['my_participation']
        if i_participate:
            instance.calendars.add(my_calendar)

        # TODO: improve Relation model in order to avoid duplication automatically + helper function
        create_relation = partial(Relation.objects.get_or_create, object_entity_id=instance.id,
                                  defaults={'user': instance.user},
                                 )

        for entities, rtype_id in ((cdata['subjects'],        constants.REL_SUB_ACTIVITY_SUBJECT),
                                   (cdata['linked_entities'], constants.REL_SUB_LINKED_2_ACTIVITY),
                                  ):
            for entity in entities:
                create_relation(subject_entity_id=entity.id, type_id=rtype_id)

        return instance

    @staticmethod
    def _create_alert(activity, trigger_date):
        from creme.assistants.models import Alert

        Alert.objects.create(user=activity.user,
                             trigger_date=trigger_date,
                             creme_entity=activity,
                             title=ugettext('Alert of activity'),
                             description=ugettext(u'Alert related to {activity}').format(activity=activity),
                            )

    def _generate_alerts(self):
        get = self.cleaned_data.get
        activity = self.instance
        alert_start = get('alert_start')

        if alert_start:
            self._create_alert(activity, alert_start)

        period = get('alert_period')
        if period:
            self._create_alert(activity, activity.start - period.as_timedelta())

    def _generate_user_messages(self):
        cdata = self.cleaned_data
        raw_users = cdata.get('informed_users')

        if raw_users:
            from creme.assistants.models import UserMessage
            from creme.assistants.constants import PRIO_NOT_IMP_PK

            activity = self.instance
            title = ugettext(u'[Creme] Activity created: {activity}').format(activity=activity)
            body = ugettext(u"""A new activity has been created: {activity}.
    Description: {description}.
    Start: {start}.
    End: {end}.
    Subjects: {subjects}.
    Participants: {participants}.""").format(
                    activity=activity,
                    description=activity.description,
                    start=activity.start or ugettext('not specified'),
                    end=activity.end or ugettext('not specified'),
                    subjects=u' / '.join(str(e) for e in cdata['subjects']),
                    participants=u' / '.join(str(c) for c in self.participants),
            )

            # TODO: sender = the real user that created the activity ???
            UserMessage.create_messages(raw_users, title, body, PRIO_NOT_IMP_PK, activity.user, activity)


class RelatedActivityCreateForm(ActivityCreateForm):
    def __init__(self, related_entity, relation_type_id, *args, **kwargs):
        # super(RelatedActivityCreateForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

        if relation_type_id == constants.REL_SUB_PART_2_ACTIVITY:
            assert isinstance(related_entity, Contact)

            if related_entity.is_user:
                self.fields['participating_users'].initial = [related_entity.is_user]
            else:
                self.fields['other_participants'].initial = [related_entity]
        elif relation_type_id == constants.REL_SUB_ACTIVITY_SUBJECT:
            self.fields['subjects'].initial = [related_entity]
        else:
            assert relation_type_id == constants.REL_SUB_LINKED_2_ACTIVITY
            self.fields['linked_entities'].initial = [related_entity]


class CalendarActivityCreateForm(ActivityCreateForm):
    class Meta(ActivityCreateForm.Meta):
        exclude = ActivityCreateForm.Meta.exclude + ('minutes', )

    def __init__(self, start=None, *args, **kwargs):
        # super(CalendarActivityCreateForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

        if start:  # Normally there's always a start_date for this kind of add
            fields = self.fields
            fields['start'].initial = start
            hour = start.hour
            minute = start.minute

            if hour or minute:  # In case start date is not a simple date (add from month view in the calendar)
                fields['start_time'].initial = time(hour=hour, minute=minute)  # Avoid 00h00 for start time in this case


class IndisponibilityCreateForm(_ActivityCreateForm):
    type_selector = ModelChoiceField(label=_('Unavailability type'), required=False,
                                     queryset=ActivitySubType.objects.filter(type=constants.ACTIVITYTYPE_INDISPO),
                                    )

    class Meta(_ActivityCreateForm.Meta):
        exclude = _ActivityCreateForm.Meta.exclude + (
                        'place', 'description', 'minutes', 'busy', 'status',
                        'duration',
                    )  # TODO: test

    blocks = _ActivityCreateForm.blocks.new(
        ('datetime',     _(u'When'),         ['is_all_day', 'start', 'start_time', 'end', 'end_time']),
        ('participants', _(u'Participants'), ['participating_users']),
    )

    def __init__(self, activity_type_id=None, *args, **kwargs):
        assert activity_type_id == constants.ACTIVITYTYPE_INDISPO
        # super(IndisponibilityCreateForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        fields = self.fields

        fields['start'].required = True

        end_f = fields['end']
        end_f.required = True
        end_f.help_text = None

        p_users_field = fields['participating_users']
        p_users_field.label = _(u'Unavailable users')
        p_users_field.required = True

    def clean(self):
        self.cleaned_data['busy'] = True
        # return super(IndisponibilityCreateForm, self).clean()
        return super().clean()

    def _get_activity_type_n_subtype(self):
        return (ActivityType.objects.get(pk=constants.ACTIVITYTYPE_INDISPO),
                self.cleaned_data['type_selector'],
               )
