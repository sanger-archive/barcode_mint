# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('barcode', '0003_numbergenerator'),
    ]

    operations = [
        migrations.DeleteModel(
            name='NumberGenerator',
        ),
    ]
