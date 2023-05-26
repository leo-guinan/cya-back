# Generated by Django 3.2.19 on 2023-05-25 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0014_query'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchengine',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='searchengine',
            name='title',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='searchengine',
            name='uuid',
            field=models.TextField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='searchablelink',
            name='uuid',
            field=models.TextField(blank=True, null=True, unique=True),
        ),
    ]
