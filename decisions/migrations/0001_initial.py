# Generated by Django 3.2.19 on 2023-05-27 14:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Fulltext',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.TextField()),
                ('title', models.TextField()),
                ('processed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('children', models.ManyToManyField(related_name='parents', to='decisions.Link')),
            ],
        ),
        migrations.CreateModel(
            name='SearchEngine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.TextField(unique=True)),
                ('url', models.TextField()),
                ('title', models.TextField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('uuid', models.TextField(blank=True, null=True, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('embedding_id', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('embeddings_saved', models.BooleanField(default=False)),
                ('snippet', models.TextField(blank=True, null=True)),
                ('fulltext', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='decisions.fulltext')),
            ],
        ),
        migrations.CreateModel(
            name='SearchEngineSearchEngine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.TextField()),
                ('slug', models.TextField(unique=True)),
                ('uuid', models.TextField(blank=True, null=True, unique=True)),
                ('search_engines', models.ManyToManyField(related_name='parents', to='decisions.SearchEngine')),
            ],
        ),
        migrations.CreateModel(
            name='SearchableLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('uuid', models.TextField(blank=True, null=True, unique=True)),
                ('image', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('search_engine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='searchable_links', to='decisions.searchengine')),
                ('url', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='searchable_links', to='decisions.link')),
            ],
        ),
        migrations.AddField(
            model_name='fulltext',
            name='url',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fulltext', to='decisions.link'),
        ),
    ]
