# Generated by Django 3.2.24 on 2024-02-14 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cofounder', '0010_auto_20240211_0111'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='complete',
            field=models.BooleanField(default=False),
        ),
    ]