# Generated by Django 3.2.25 on 2024-04-26 13:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0008_company_team_teammember'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='description',
        ),
        migrations.RemoveField(
            model_name='team',
            name='name',
        ),
        migrations.RemoveField(
            model_name='team',
            name='title',
        ),
    ]
