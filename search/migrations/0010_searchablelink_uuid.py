# Generated by Django 3.2.18 on 2023-04-22 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0009_searchablelink_searchengine'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchablelink',
            name='uuid',
            field=models.TextField(blank=True, null=True),
        ),
    ]
