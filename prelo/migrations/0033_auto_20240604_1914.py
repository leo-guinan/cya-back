# Generated by Django 3.2.25 on 2024-06-04 19:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0032_investmentfirm_lookup_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dealmemo',
            name='company',
        ),
        migrations.RemoveField(
            model_name='investorreport',
            name='company',
        ),
    ]
