# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-12 12:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoping', '0010_auto_20161212_1211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wosarticle',
            name='bp',
            field=models.CharField(max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='wosarticle',
            name='ep',
            field=models.CharField(max_length=5, null=True),
        ),
    ]