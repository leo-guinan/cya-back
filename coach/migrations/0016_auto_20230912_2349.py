# Generated by Django 3.2.20 on 2023-09-12 23:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coach', '0015_sourcelink'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sourcelink',
            name='fulltext_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
