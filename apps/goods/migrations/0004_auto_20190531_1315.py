# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0003_auto_20190531_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goods',
            name='detail',
            field=models.TextField(max_length=250, blank=True, verbose_name='商品详情'),
        ),
    ]
