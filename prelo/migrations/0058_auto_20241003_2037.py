# Generated by Django 3.2.25 on 2024-10-03 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0057_auto_20241003_2021'),
    ]

    operations = [
        migrations.AddField(
            model_name='investmentfirm',
            name='name',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='investmentfirm',
            name='website',
            field=models.TextField(blank=True, null=True),
        ),
    ]