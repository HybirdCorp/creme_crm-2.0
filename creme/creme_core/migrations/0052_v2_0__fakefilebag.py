# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('creme_core', '0051_v2_0__set_version'),
    ]

    operations = [
        migrations.CreateModel(
            name='FakeFileBag',
            fields=[
                ('cremeentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False,
                                                         to='creme_core.CremeEntity', on_delete=models.CASCADE,
                                                        )
                ),
                ('name', models.CharField(max_length=100, null=True, verbose_name='Name', blank=True)),
                ('file1', models.ForeignKey(on_delete=models.PROTECT, verbose_name='First file',
                                            to='creme_core.FakeFileComponent',
                                            null=True, blank=True,
                                           )
                ),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Test File bag',
                'verbose_name_plural': 'Test File bags',
            },
            bases=('creme_core.cremeentity',),
        ),
    ]
