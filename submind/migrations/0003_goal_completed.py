# Generated by Django 3.2.25 on 2024-04-18 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submind', '0002_goal_question_thought'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='completed',
            field=models.BooleanField(default=False),
        ),
    ]