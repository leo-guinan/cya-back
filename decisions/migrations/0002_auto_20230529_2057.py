# Generated by Django 3.2.19 on 2023-05-29 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('decisions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetaSearchEngine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.TextField()),
                ('slug', models.TextField(unique=True)),
                ('uuid', models.TextField(blank=True, null=True, unique=True)),
                ('children', models.ManyToManyField(related_name='parents', to='decisions.MetaSearchEngine')),
                ('search_engines', models.ManyToManyField(related_name='parents', to='decisions.SearchEngine')),
            ],
        ),
        migrations.DeleteModel(
            name='SearchEngineSearchEngine',
        ),
    ]
