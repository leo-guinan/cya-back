# Generated by Django 3.2.24 on 2024-03-21 17:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0002_task_priority'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='details',
            new_name='description',
        ),
    ]