# Generated by Django 3.2.18 on 2023-04-22 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0011_searchablelink_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchengine',
            name='slug',
            field=models.TextField(unique=True),
        ),
    ]
