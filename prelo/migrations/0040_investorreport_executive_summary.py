# Generated by Django 3.2.25 on 2024-07-10 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0039_auto_20240709_1339'),
    ]

    operations = [
        migrations.AddField(
            model_name='investorreport',
            name='executive_summary',
            field=models.TextField(blank=True, null=True),
        ),
    ]
