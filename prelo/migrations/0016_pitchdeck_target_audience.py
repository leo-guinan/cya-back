# Generated by Django 3.2.25 on 2024-05-08 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0015_auto_20240427_1843'),
    ]

    operations = [
        migrations.AddField(
            model_name='pitchdeck',
            name='target_audience',
            field=models.TextField(default='Founder'),
        ),
    ]
