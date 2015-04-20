# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

import creme.creme_core.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ('crudity', '0001_initial'),
        ('creme_core', '0003_v1_6__convert_old_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='history',
            name='user',
            field=creme.creme_core.models.fields.CremeUserForeignKey(default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Owner'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='waitingaction',
            name='user',
            field=creme.creme_core.models.fields.CremeUserForeignKey(default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Owner'),
            preserve_default=True,
        ),
    ]