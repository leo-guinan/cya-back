# Generated by Django 3.2.20 on 2023-10-12 22:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cofounder', '0006_source_fulltext_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='cofounder.user'),
        ),
    ]
