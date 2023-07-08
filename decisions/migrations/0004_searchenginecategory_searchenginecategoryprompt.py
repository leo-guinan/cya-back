# Generated by Django 3.2.19 on 2023-06-10 22:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_auto_20230529_2057'),
        ('decisions', '0003_delete_searchablelink'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchEngineCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client_app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='search_engine_categories', to='chat.clientapp')),
                ('search_engine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='decisions.searchengine')),
            ],
        ),
        migrations.CreateModel(
            name='SearchEngineCategoryPrompt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client_app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='search_engine_category_prompt', to='chat.clientapp')),
                ('search_engine_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prompts', to='decisions.searchenginecategory')),
            ],
        ),
    ]
