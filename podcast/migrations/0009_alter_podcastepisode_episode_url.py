# Generated by Django 3.2.25 on 2024-04-15 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcast', '0008_podcastquery_error'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podcastepisode',
            name='episode_url',
            field=models.TextField(blank=True, null=True),
        ),
    ]
