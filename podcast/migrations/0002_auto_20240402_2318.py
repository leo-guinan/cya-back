# Generated by Django 3.2.25 on 2024-04-02 23:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcast', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='external_id',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='podcastepisode',
            name='transcript_guid',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
