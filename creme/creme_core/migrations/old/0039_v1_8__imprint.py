# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-18 08:59
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from django.db.models.deletion import CASCADE


class Migration(migrations.Migration):
    dependencies = [
        ('creme_core', '0038_v1_8__fileref'),
    ]

    operations = [
        migrations.CreateModel(
            name='Imprint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('entity', models.ForeignKey(on_delete=CASCADE, related_name='imprints', to='creme_core.CremeEntity')),
                ('user', models.ForeignKey(on_delete=CASCADE, related_name='imprints', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
