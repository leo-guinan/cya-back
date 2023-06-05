# Generated by Django 3.2.19 on 2023-05-29 18:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0001_initial'),
        ('chat', '0003_clientapp_default_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientapp',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='apps', to='client.client'),
        ),
    ]