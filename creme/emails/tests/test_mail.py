# -*- coding: utf-8 -*-

try:
    from datetime import timedelta
    from functools import partial
    from os.path import basename
    from tempfile import NamedTemporaryFile

    from django.conf import settings
    from django.core import mail
    from django.core.mail.backends.locmem import EmailBackend
    from django.urls import reverse
    from django.utils.timezone import now
    from django.utils.translation import ugettext as _

    from creme.creme_core.auth.entity_credentials import EntityCredentials
    from creme.creme_core.core.job import JobManagerQueue  # Should be a test queue
    from creme.creme_core.models import Relation, SetCredentials, FieldsConfig, Job
    from creme.creme_core.forms.widgets import Label

    from creme.persons.tests.base import skipIfCustomContact, skipIfCustomOrganisation

    from creme.documents.models import FolderCategory

    from .base import (_EmailsTestCase, skipIfCustomEntityEmail, skipIfCustomEmailTemplate,
            Contact, Organisation, Document, Folder, EntityEmail, EmailTemplate)
    from ..constants import (MAIL_STATUS_NOTSENT, MAIL_STATUS_SENT,
            MAIL_STATUS_SENDINGERROR, REL_SUB_MAIL_RECEIVED, REL_SUB_MAIL_SENDED)
    from ..creme_jobs import entity_emails_send_type
    from ..models import EmailSignature
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


@skipIfCustomEntityEmail
class EntityEmailTestCase(_EmailsTestCase):
    @classmethod
    def setUpClass(cls):
        # super(EntityEmailTestCase, cls).setUpClass()
        super().setUpClass()
        cls.original_send_messages = EmailBackend.send_messages

    def tearDown(self):
        # super(EntityEmailTestCase, self).tearDown()
        super().tearDown()
        EmailBackend.send_messages = self.original_send_messages

    def login(self, is_superuser=True, is_staff=False,
              allowed_apps=('persons', 'emails'),
              creatable_models=(Contact, Organisation, EntityEmail),
              *args, **kwargs):
        # return super(EntityEmailTestCase, self).login(is_superuser=is_superuser,
        return super().login(is_superuser=is_superuser,
                             allowed_apps=allowed_apps,
                             creatable_models=creatable_models,
                             *args, **kwargs
                            )

    def _build_send_from_template_url(self, entity):
        return reverse('emails__create_email_from_template', args=(entity.id,))

    def _get_job(self):
        return self.get_object_or_fail(Job, type_id=entity_emails_send_type.id)

    def _send_mails(self, job=None):
        entity_emails_send_type.execute(job or self._get_job())

    @skipIfCustomContact
    def test_createview01(self):
        user = self.login()

        queue = JobManagerQueue.get_main_queue()
        queue.clear()

        recipient = 'vincent.law@immigrates.rmd'
        contact = Contact.objects.create(user=user, first_name='Vincent', last_name='Law', email=recipient)
        url = self._build_create_entitymail_url(contact)

        context = self.assertGET200(url).context
        # self.assertEqual(_('Sending an email to «%s»') % contact, context.get('title'))
        self.assertEqual(_('Sending an email to «{}»').format(contact), context.get('title'))
        self.assertEqual(EntityEmail.sending_label,                     context.get('submit_label'))

        with self.assertNoException():
            c_recipients = context['form'].fields['c_recipients']

        self.assertEqual([contact.id], c_recipients.initial)

        sender = user.linked_contact.email
        body = 'Freeze !'
        body_html = '<p>Freeze !</p>'
        subject = 'Under arrest'
        response = self.client.post(
            url,
            data={'user':         user.id,
                  'sender':       sender,
                  'c_recipients': self.formfield_value_multi_creator_entity(contact),
                  'subject':      subject,
                  'body':         body,
                  'body_html':    body_html,
                 }
        )
        self.assertNoFormError(response)

        email = self.get_object_or_fail(EntityEmail, sender=sender, recipient=recipient)
        self.assertEqual(user,             email.user)
        self.assertEqual(subject,          email.subject)
        self.assertEqual(body,             email.body)
        self.assertEqual(body_html,        email.body_html)
        self.assertEqual(MAIL_STATUS_SENT, email.status)

        self.get_object_or_fail(Relation, subject_entity=email, type=REL_SUB_MAIL_SENDED,   object_entity=user.linked_contact)
        self.get_object_or_fail(Relation, subject_entity=email, type=REL_SUB_MAIL_RECEIVED, object_entity=contact)

        response = self.assertGET200(reverse('emails__view_email', args=(email.id,)))
        self.assertTemplateUsed(response, 'emails/view_entity_mail.html')

        response = self.assertGET200(reverse('emails__view_email_popup', args=(email.id,)))
        self.assertTemplateUsed(response, 'emails/view_entity_mail_popup.html')

        messages = mail.outbox
        self.assertEqual(1, len(messages))

        message = messages[0]
        self.assertEqual(subject,                    message.subject)
        self.assertEqual(body,                       message.body)
        self.assertEqual([recipient],                message.recipients())
        self.assertEqual(sender,                     message.from_email)
        self.assertEqual([(body_html, 'text/html')], message.alternatives)
        self.assertFalse(message.attachments)

        self.assertEqual([], queue.refreshed_jobs)

    @skipIfCustomOrganisation
    def test_createview02(self):
        "Attachments"
        user = self.login()

        recipient = 'contact@venusgate.jp'
        orga = Organisation.objects.create(user=user, name='Venus gate', email=recipient)
        url = self._build_create_entitymail_url(orga)

        response = self.assertGET200(url)

        with self.assertNoException():
            o_recipients = response.context['form'].fields['o_recipients']

        self.assertEqual([orga.id], o_recipients.initial)

        folder = Folder.objects.create(user=user, title='Test folder', parent_folder=None,
                                       category=FolderCategory.objects.create(name='Test category'),
                                      )

        def create_doc(title, content):
            tmpfile = NamedTemporaryFile(suffix=".txt")
            tmpfile.write(content)
            tmpfile.flush()
            tmpfile.file.seek(0)

            response = self.client.post(reverse('documents__create_document'), follow=True,
                                        data={'user':        user.id,
                                              'title':       title,
                                              'description': 'Attachment file',
                                              'filedata':    tmpfile,
                                              'linked_folder': folder.id,
                                             }
                                       )
            self.assertNoFormError(response)

            return self.get_object_or_fail(Document, title=title)

        content1 = b"Hey I'm the content"
        content2 = b'Another content'
        doc1 = create_doc('Doc01', content1)
        doc2 = create_doc('Doc02', content2)

        sender = 're-l.mayer@rpd.rmd'
        signature = EmailSignature.objects.create(user=user, name="Re-l's signature", body='I love you... not')
        response = self.client.post(url, data={'user':         user.id,
                                               'sender':       sender,
                                               'o_recipients': self.formfield_value_multi_creator_entity(orga),
                                               'subject':      'Cryogenisation',
                                               'body':         'I want to be freezed !',
                                               'body_html':    '<p>I want to be freezed !</p>',
                                               'signature':    signature.id,
                                               'attachments':  self.formfield_value_multi_creator_entity(doc1, doc2),
                                               'send_me':      True,
                                              }
                                   )
        self.assertNoFormError(response)

        email = self.get_object_or_fail(EntityEmail, sender=sender, recipient=recipient)
        self.assertEqual(signature, email.signature)

        email = self.get_object_or_fail(EntityEmail, sender=sender, recipient=sender)
        self.assertEqual(signature, email.signature)

        messages = mail.outbox
        self.assertEqual(2, len(messages))
        self.assertEqual([sender], messages[0].recipients())

        message = messages[1]
        self.assertEqual([recipient], message.recipients())
        self.assertEqual([(basename(doc1.filedata.name), content1.decode(), 'text/plain'),
                          (basename(doc2.filedata.name), content2.decode(), 'text/plain'),
                         ],
                         message.attachments
                        )

    @skipIfCustomContact
    @skipIfCustomOrganisation
    def test_createview03(self):
        "Invalid email address"
        user = self.login()

        create_contact = partial(Contact.objects.create, user=user)
        contact01 = create_contact(first_name='Vincent', last_name='Law',
                                   email='vincent.law@immigrates',  # Invalid
                                  )
        contact02 = create_contact(first_name='Pino', last_name='AutoReiv',
                                   email='pino@autoreivs.rmd', #ok
                                  )

        create_orga = partial(Organisation.objects.create, user=user)
        orga01 = create_orga(name='Venus gate', email='contact/venusgate.jp')  # Invalid
        orga02 = create_orga(name='Nerv',       email='contact@nerv.jp')  # Ok

        response = self.assertPOST200(
            self._build_create_entitymail_url(contact01),
            data={'user':         user.id,
                  'sender':       user.linked_contact.email,
                  'c_recipients': self.formfield_value_multi_creator_entity(contact01, contact02),
                  'o_recipients': self.formfield_value_multi_creator_entity(orga01, orga02),
                  'subject':      'Under arrest',
                  'body':         'Freeze !',
                  'body_html':    '<p>Freeze !</p>',
                 },
        )
        self.assertFormError(response, 'form', 'c_recipients',
                             _('The email address for {} is invalid').format(contact01)
                            )
        self.assertFormError(response, 'form', 'o_recipients',
                             _('The email address for {} is invalid').format(orga01)
                            )

    @skipIfCustomContact
    def test_createview04(self):
        "Related contact has no emails address"
        user = self.login()

        contact = Contact.objects.create(user=user, first_name='Vincent', last_name='Law')
        response = self.assertGET200(self._build_create_entitymail_url(contact))

        with self.assertNoException():
            c_recipients = response.context['form'].fields['c_recipients']

        self.assertIsNone(c_recipients.initial)
        self.assertEqual(_('Beware: the contact «{}» has no email address!').format(contact),
                         c_recipients.help_text
                        )

    @skipIfCustomOrganisation
    def test_createview05(self):
        "Related organisation has no email address"
        user = self.login()

        orga = Organisation.objects.create(user=user, name='Venus gate')
        response = self.assertGET200(self._build_create_entitymail_url(orga))

        with self.assertNoException():
            o_recipients = response.context['form'].fields['o_recipients']

        self.assertIsNone(o_recipients.initial)
        self.assertEqual(_('Beware: the organisation «{}» has no email address!').format(orga),
                         o_recipients.help_text
                        )

    @skipIfCustomContact
    @skipIfCustomOrganisation
    def test_createview06(self):
        "Credentials problem"
        user = self.login(is_superuser=False)

        create_sc = partial(SetCredentials.objects.create, role=user.role)
        create_sc(value=(EntityCredentials.VIEW   | EntityCredentials.CHANGE |
                         EntityCredentials.LINK   |
                         EntityCredentials.DELETE | EntityCredentials.UNLINK
                        ),
                  set_type=SetCredentials.ESET_OWN
                 )
        create_sc(value=(EntityCredentials.VIEW   | EntityCredentials.CHANGE |
                         EntityCredentials.DELETE | EntityCredentials.UNLINK
                        ),  # Not LINK
                  set_type=SetCredentials.ESET_ALL
                 )

        create_contact = Contact.objects.create
        contact01 = create_contact(user=self.other_user, first_name='Vincent', 
                                   last_name='Law', email='vincent.law@immigrates.rmd',
                                  )
        contact02 = create_contact(user=user, first_name='Pino', last_name='AutoReiv',
                                   email='pino@autoreivs.rmd',
                                  )

        create_orga = Organisation.objects.create
        orga01 = create_orga(user=self.other_user, name='Venus gate', email='contact@venusgate.jp')
        orga02 = create_orga(user=user, name='Nerv', email='contact@nerv.jp')

        self.assertTrue(user.has_perm_to_view(contact01))
        self.assertFalse(user.has_perm_to_link(contact01))
        self.assertTrue(user.has_perm_to_view(contact02))
        self.assertTrue(user.has_perm_to_link(contact02))

        def post(contact):
            return self.client.post(
                self._build_create_entitymail_url(contact),
                data={'user':         user.id,
                      'sender':       user.linked_contact.email,
                      'c_recipients': self.formfield_value_multi_creator_entity(contact01, contact02),
                      'o_recipients': self.formfield_value_multi_creator_entity(orga01, orga02),
                      'subject':      'Under arrest',
                      'body':         'Freeze !',
                      'body_html':    '<p>Freeze !</p>',
                     }
            )

        self.assertEqual(403, post(contact01).status_code)

        response = post(contact02)
        self.assertEqual(200, response.status_code)

        self.assertFormError(response, 'form', 'c_recipients',
                             _('Some entities are not linkable: {}').format(contact01)
                            )
        self.assertFormError(response, 'form', 'o_recipients',
                             _('Some entities are not linkable: {}').format(orga01)
                            )

    def test_createview07(self):
        "No recipent"
        user = self.login()
        c = Contact.objects.create(user=user, first_name='Vincent', last_name='Law')
        response = self.assertPOST200(self._build_create_entitymail_url(c),
                                      data={'user':         user.id,
                                            'sender':       user.linked_contact.email,
                                            'c_recipients': '[]',
                                            'o_recipients': '[]',
                                            'subject':      'Under arrest',
                                            'body':         'Freeze !',
                                            'body_html':    '<p>Freeze !</p>',
                                           }
                                      )
        self.assertFormError(response, 'form', None,
                             _('Select at least a Contact or an Organisation')
                            )

    @skipIfCustomContact
    def test_createview08(self):
        "FieldsConfig: Contact.email is hidden"
        user = self.login()
        FieldsConfig.create(Contact,
                            descriptions=[('email', {FieldsConfig.HIDDEN: True})],
                           )

        c = Contact.objects.create(user=user, first_name='Vincent', last_name='Law')

        url = self._build_create_entitymail_url(c)
        response = self.assertGET200(url)

        with self.assertNoException():
            recip_field = response.context['form'].fields['c_recipients']

        self.assertIsInstance(recip_field.widget, Label)
        self.assertEqual(_('Beware: the field «Email address» is hidden ; please contact your administrator.'),
                         recip_field.initial
                        )

        response = self.assertPOST200(url,
                                      data={'user':         user.id,
                                            'sender':       user.linked_contact.email,
                                            'c_recipients': self.formfield_value_multi_creator_entity(c),  # Should not be used
                                            'subject':      'Under arrest',
                                            'body':         'Freeze !',
                                            'body_html':    '<p>Freeze !</p>',
                                           }
                                     )
        self.assertFormError(response, 'form', None,
                             _('Select at least a Contact or an Organisation')
                            )

    @skipIfCustomOrganisation
    def test_createview09(self):
        "FieldsConfig: Organisation.email is hidden"
        user = self.login()
        FieldsConfig.create(Organisation,
                            descriptions=[('email', {FieldsConfig.HIDDEN: True})],
                           )

        orga = Organisation.objects.create(user=user, name='Venus gate')

        url = self._build_create_entitymail_url(orga)
        response = self.assertGET200(url)

        with self.assertNoException():
            recip_field = response.context['form'].fields['o_recipients']

        self.assertIsInstance(recip_field.widget, Label)
        self.assertEqual(_('Beware: the field «Email address» is hidden ; please contact your administrator.'),
                         recip_field.initial
                        )

        response = self.assertPOST200(
            url,
            data={'user':         user.id,
                  'sender':       user.linked_contact.email,
                  'o_recipients': self.formfield_value_multi_creator_entity(orga),  # Should not be used
                  'subject':      'Under arrest',
                  'body':         'Freeze !',
                  'body_html':    '<p>Freeze !</p>',
                 },
        )
        self.assertFormError(response, 'form', None,
                             _('Select at least a Contact or an Organisation')
                            )

    @skipIfCustomContact
    def test_createview10(self):
        "Mail sending error"
        user = self.login()

        queue = JobManagerQueue.get_main_queue()
        queue.clear()

        self.send_messages_called = False

        def send_messages(this, messages):
            self.send_messages_called = True
            raise Exception('Sent error')

        EmailBackend.send_messages = send_messages

        recipient = 'vincent.law@immigrates.rmd'
        contact = Contact.objects.create(user=user, first_name='Vincent',
                                         last_name='Law', email=recipient,
                                        )

        sender = user.linked_contact.email
        response = self.client.post(self._build_create_entitymail_url(contact),
                                    data={'user':         user.id,
                                          'sender':       sender,
                                          'c_recipients': self.formfield_value_multi_creator_entity(contact),
                                          'subject':      'Under arrest',
                                          'body':         'Freeze !',
                                          'body_html':    '<p>Freeze !</p>',
                                         }
                                    )
        self.assertNoFormError(response)

        email = self.get_object_or_fail(EntityEmail, sender=sender, recipient=recipient)
        self.assertEqual(MAIL_STATUS_SENDINGERROR, email.status)

        self.assertTrue(queue.refreshed_jobs)

    @skipIfCustomContact
    @skipIfCustomOrganisation
    def test_createview11(self):
        "No creation credentials"
        user = self.login(is_superuser=False,
                          creatable_models=(Contact, Organisation)  # No EntityEmail
                         )
        SetCredentials.objects.create(
            role=user.role,
            value=(EntityCredentials.VIEW   | EntityCredentials.CHANGE |
                   EntityCredentials.LINK   |
                   EntityCredentials.DELETE | EntityCredentials.UNLINK
                  ),
            set_type=SetCredentials.ESET_ALL,
        )

        contact02 = Contact.objects.create(user=user, first_name='Pino', last_name='AutoReiv')
        self.assertGET403(self._build_create_entitymail_url(contact02))

    @skipIfCustomContact
    @skipIfCustomOrganisation
    def test_createview_empty_email(self):
        "Empty email address"
        user = self.login()

        create_contact = partial(Contact.objects.create, user=user)
        # contact01 = create_contact(first_name='Vincent', last_name='Law',email=None)
        contact01 = create_contact(first_name='Vincent', last_name='Law', email='')
        contact02 = create_contact(first_name='Pino', last_name='AutoReiv', email='pino@autoreivs.rmd')

        create_orga = partial(Organisation.objects.create, user=user)
        orga01 = create_orga(name='Venus gate', email='')
        orga02 = create_orga(name='Nerv',       email='contact@nerv.jp')  # Ok

        response = self.assertPOST200(
            self._build_create_entitymail_url(contact01),
            data={'user':         user.id,
                  'sender':       user.linked_contact.email,
                  'c_recipients': self.formfield_value_multi_creator_entity(contact01, contact02),
                  'o_recipients': self.formfield_value_multi_creator_entity(orga01, orga02),
                  'subject':      'Under arrest',
                  'body':         'Freeze !',
                  'body_html':    '<p>Freeze !</p>',
                 },
        )
        self.assertFormError(response, 'form', 'c_recipients',
                             _('This entity does not exist.')
                            )
        self.assertFormError(response, 'form', 'o_recipients',
                             _('This entity does not exist.')
                            )

    @skipIfCustomEmailTemplate
    @skipIfCustomContact
    def test_create_from_template01(self):
        user = self.login()

        body_format      = 'Hi {} {}, nice to meet you !'.format
        body_html_format = 'Hi <strong>{} {}</strong>, nice to meet you !'.format

        subject   = 'I am da subject'
        signature = EmailSignature.objects.create(user=user, name="Re-l's signature", body='I love you... not')
        template = EmailTemplate.objects.create(user=user, name='My template',
                                                subject=subject,
                                                body=body_format('{{first_name}}', '{{last_name}}'),
                                                body_html=body_html_format('{{first_name}}', '{{last_name}}'),
                                                signature=signature,
                                               )

        recipient = 'vincent.law@city.mosk'
        first_name = 'Vincent'
        last_name = 'Law'
        contact = Contact.objects.create(user=user, first_name=first_name, last_name=last_name, email=recipient)

        url = self._build_send_from_template_url(contact)
        self.assertGET200(url)

        response = self.client.post(url, data={'step':     1,
                                               'template': template.id,
                                              }
                                   )
        self.assertNoFormError(response)

        with self.assertNoException():
            form = response.context['form']
            fields = form.fields
            fields['subject']
            fields['body']
            fields['body_html']
            fields['signature']
            fields['attachments']

        self.assertEqual(2, fields['step'].initial)

        ini_get = form.initial.get
        self.assertEqual(subject, ini_get('subject'))
        self.assertEqual(body_format(contact.first_name, contact.last_name),      ini_get('body'))
        self.assertEqual(body_html_format(contact.first_name, contact.last_name), ini_get('body_html'))
        self.assertEqual(signature.id, ini_get('signature'))
        # self.assertEqual(attachments,  ini_get('attachments')) #TODO

        response = self.client.post(url, data={'step':         2,
                                               'user':         user.id,
                                               'sender':       user.linked_contact.email,
                                               'c_recipients': self.formfield_value_multi_creator_entity(contact),
                                               'subject':      subject,
                                               'body':         ini_get('body'),
                                               'body_html':    ini_get('body_html'),
                                               'signature':    signature.id,
                                              }
                                   )
        self.assertNoFormError(response)
        self.get_object_or_fail(EntityEmail, recipient=recipient)

    def test_listview01(self):
        self.login()
        self._create_emails()

        response = self.assertGET200(reverse('emails__list_emails'))

        with self.assertNoException():
            emails = response.context['entities']

        self.assertEqual(4, emails.object_list.count())

    def _create_email(self, status=MAIL_STATUS_NOTSENT, body_html=''):
        user = self.user
        return EntityEmail.objects.create(user=user,
                                          sender=user.linked_contact.email,
                                          recipient='vincent.law@immigrates.rmd',
                                          subject='Under arrest',
                                          body='Freeze !',
                                          status=status,
                                          body_html=body_html,
                                         )

    def test_get_sanitized_html_field01(self):
        "Empty body"
        self.login()
        email = self._create_email()
        self.assertGET409(reverse('creme_core__sanitized_html_field', args=(email.id, 'sender')))  # Not an UnsafeHTMLField

        response = self.assertGET200(reverse('creme_core__sanitized_html_field', args=(email.id, 'body_html')))
        self.assertEqual(b'', response.content)

    def test_get_sanitized_html_field02(self):
        self.login()
        email = self._create_email(body_html='<p>hi</p>'
                                             '<img alt="Totoro" src="http://external/images/totoro.jpg" />'
                                             '<img alt="Nekobus" src="{}nekobus.jpg" />'.format(settings.MEDIA_URL)
                                  )

        url = reverse('creme_core__sanitized_html_field', args=(email.id, 'body_html'))
        response = self.assertGET200(url)
        self.assertEqual('<p>hi</p>'
                         '<img alt="Totoro">'
                         '<img alt="Nekobus" src="{}nekobus.jpg">'.format(settings.MEDIA_URL),
                         response.content.decode()
                        )

        response = self.assertGET200(url + '?external_img=on')
        self.assertEqual('<p>hi</p>'
                         '<img alt="Totoro" src="http://external/images/totoro.jpg">'
                         '<img alt="Nekobus" src="{}nekobus.jpg">'.format(settings.MEDIA_URL),
                         response.content.decode()
                        )
        # TODO: improve sanitization test (other tags, css...)

    def test_job01(self):
        self.login()
        now_value = now()

        job = self._get_job()
        self.assertIsNone(job.user)
        self.assertIsNone(job.type.next_wakeup(job, now_value))

        email = self._create_email(MAIL_STATUS_NOTSENT)
        self.assertIs(job.type.next_wakeup(job, now_value), now_value)

        self._send_mails(job)

        messages = mail.outbox
        self.assertEqual(1, len(messages))

        message = messages[0]
        self.assertEqual(email.subject, message.subject)
        self.assertEqual(email.body,    message.body)

    def test_job02(self):
        from ..creme_jobs.entity_emails_send import ENTITY_EMAILS_RETRY

        self.login()
        email = self._create_email(MAIL_STATUS_SENDINGERROR)

        job = self._get_job()
        now_value = now()
        wakeup = job.type.next_wakeup(job, now_value)
        self.assertIsNotNone(wakeup)
        self.assertDatetimesAlmostEqual(now_value + timedelta(minutes=ENTITY_EMAILS_RETRY),
                                        wakeup
                                       )

        self._send_mails(job)

        messages = mail.outbox
        self.assertEqual(1, len(messages))

        message = messages[0]
        self.assertEqual(email.subject, message.subject)
        self.assertEqual(email.body,    message.body)

    def test_job03(self):
        self.login()
        self._create_email(MAIL_STATUS_SENT)
        self._send_mails()

        self.assertFalse(mail.outbox)

    def test_job04(self):
        "Email is in the trash"
        self.login()
        email = self._create_email(MAIL_STATUS_SENDINGERROR)
        email.trash()

        job = self._get_job()
        self.assertIsNone(job.type.next_wakeup(job, now()))

        self._send_mails(job)
        self.assertFalse(mail.outbox)

    def test_refresh_job01(self):
        "Mail is restored + have to be send => refresh the job"
        self.login()
        job = self._get_job()

        email = self._create_email(MAIL_STATUS_SENDINGERROR)
        email.trash()

        queue = JobManagerQueue.get_main_queue()
        queue.clear()

        email.restore()
        self.assertFalse(self.refresh(email).is_deleted)

        jobs = queue.refreshed_jobs
        self.assertEqual(1, len(jobs))
        self.assertEqual(job, jobs[0][0])

    def test_refresh_job02(self):
        "Mail is restored + do not have to be send => do not refresh the job"
        self.login()

        email = self._create_email(MAIL_STATUS_SENDINGERROR)
        email.status = MAIL_STATUS_SENT
        email.is_deleted = True
        email.save()

        email = self.refresh(email)

        queue = JobManagerQueue.get_main_queue()
        queue.clear()

        email.restore()
        self.assertFalse(queue.refreshed_jobs)

    # TODO: test other views
