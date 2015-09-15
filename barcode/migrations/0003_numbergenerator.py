# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('barcode', '0002_auto_20150915_1319'),
    ]

    operations = [
        migrations.CreateModel(
            name='NumberGenerator',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
            ],
        ),
    ]
