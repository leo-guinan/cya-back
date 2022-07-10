# Generated by Django 3.2.13 on 2022-07-09 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unfollow', '0011_alter_analysis_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='dormant_count',
            field=models.IntegerField(default=0, verbose_name='number of accounts followed that are dormant'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='following_count',
            field=models.IntegerField(default=0, verbose_name='number of accounts followed'),
        ),
    ]
