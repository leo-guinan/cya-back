# Generated by Django 3.2.20 on 2023-10-12 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cofounder', '0004_businessprofile_business_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='content_type',
            field=models.CharField(choices=[('PC', 'Podcast'), ('YT', 'Youtube'), ('BL', 'blog'), ('TX', 'text')], default='TX', max_length=2),
        ),
        migrations.AlterField(
            model_name='source',
            name='rss_feed',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
