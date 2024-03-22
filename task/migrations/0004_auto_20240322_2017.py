# Generated by Django 3.2.24 on 2024-03-22 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0003_rename_details_task_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='external_model_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='external_object_uuid',
            field=models.TextField(blank=True, null=True),
        ),
    ]