# Generated by Django 3.2.19 on 2023-05-26 21:45

import chat.enums
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('search', '0015_auto_20230525_2123'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientApp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
                ('api_key', models.TextField(unique=True)),
                ('initial_message', models.TextField(default='How can I help you today?')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('speaker', models.IntegerField(choices=[(1, 'HUMAN'), (2, 'BOT'), (3, 'SYSTEM')], default=chat.enums.SpeakerTypes['HUMAN'])),
                ('previous_message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='next_messages', to='chat.message')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.TextField()),
                ('title', models.TextField()),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='chat.clientapp')),
                ('search_engine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='search.searchengine')),
            ],
        ),
        migrations.CreateModel(
            name='Use',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField(default=0)),
                ('messages', models.ManyToManyField(related_name='uses', to='chat.Message')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uses', to='chat.source')),
            ],
        ),
    ]
