# Generated by Django 3.2.25 on 2024-04-25 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0005_auto_20240425_2028'),
    ]

    operations = [
        migrations.AddField(
            model_name='pitchdeck',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
