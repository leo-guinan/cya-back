# Generated by Django 3.2.25 on 2024-04-26 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0009_auto_20240426_1306'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='competition',
            field=models.TextField(blank=True, null=True),
        ),
    ]