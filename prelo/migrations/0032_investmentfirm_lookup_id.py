# Generated by Django 3.2.25 on 2024-06-04 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0031_investor_lookup_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='investmentfirm',
            name='lookup_id',
            field=models.IntegerField(default=1, unique=True),
            preserve_default=False,
        ),
    ]
