# Generated by Django 3.2.18 on 2023-04-01 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_link_processed'),
    ]

    operations = [
        migrations.AddField(
            model_name='section',
            name='embeddings_saved',
            field=models.BooleanField(default=False),
        ),
    ]