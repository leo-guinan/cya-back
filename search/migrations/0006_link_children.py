# Generated by Django 3.2.18 on 2023-04-02 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0005_alter_fulltext_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='link',
            name='children',
            field=models.ManyToManyField(related_name='parents', to='search.Link'),
        ),
    ]
