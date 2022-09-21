# Generated by Django 3.2.13 on 2022-09-21 23:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0011_media'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountError',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Error encountered')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date error occurred')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='errors', to='twitter.twitteraccount')),
            ],
        ),
    ]
