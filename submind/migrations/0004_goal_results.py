# Generated by Django 3.2.25 on 2024-04-18 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submind', '0003_goal_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='results',
            field=models.TextField(blank=True, null=True),
        ),
    ]
