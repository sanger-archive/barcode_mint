# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('barcode', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='barcode',
            name='uuid',
            field=models.UUIDField(unique=True, default=uuid.uuid4),
        ),
    ]
