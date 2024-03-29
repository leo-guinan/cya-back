# Generated by Django 3.2.24 on 2024-02-17 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cofounder', '0011_task_complete'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='completedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='scope',
            field=models.CharField(choices=[('PR', 'Private'), ('PB', 'Public'), ('LM', 'Limited')], default='PR', max_length=2),
        ),
    ]
