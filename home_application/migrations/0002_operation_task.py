# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-05-16 15:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='operation',
            name='task',
            field=models.CharField(default='unknown', max_length=60),
        ),
    ]
