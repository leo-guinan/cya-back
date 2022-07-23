# Generated by Django 3.2.13 on 2022-07-20 02:27

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('friendcontent', '0002_auto_20220720_0143'),
    ]

    operations = [
        migrations.AddField(
            model_name='triggertweet',
            name='added',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='time the record was added'),
            preserve_default=False,
        ),
    ]
