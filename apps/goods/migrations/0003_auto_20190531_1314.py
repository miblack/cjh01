# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0002_auto_20190531_1147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goods',
            name='detail',
            field=models.CharField(blank=True, max_length=250, verbose_name='商品详情'),
        ),
    ]
