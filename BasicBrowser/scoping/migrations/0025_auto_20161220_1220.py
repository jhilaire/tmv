# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-20 12:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoping', '0024_auto_20161219_1039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wosarticle',
            name='bp',
            field=models.CharField(max_length=10, null=True, verbose_name='Beginning Page'),
        ),
    ]
