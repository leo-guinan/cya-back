# Generated by Django 3.2.20 on 2023-09-23 20:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChatPrompt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt', models.TextField()),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='InitialQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=255)),
                ('index', models.IntegerField()),
                ('prompt_variable', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('rss_feed', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('content_type', models.CharField(choices=[('PC', 'Podcast'), ('YT', 'Youtube'), ('BL', 'blog')], default='BL', max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.CharField(max_length=255)),
                ('preferred_name', models.CharField(max_length=255)),
                ('initial_session_id', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='UserPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('daily_checkin', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='cofounder.user')),
            ],
        ),
        migrations.CreateModel(
            name='UserAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cofounder.initialquestion')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cofounder.user')),
            ],
        ),
        migrations.CreateModel(
            name='SourceLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=255, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('fulltext_id', models.CharField(blank=True, max_length=255, null=True)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='cofounder.source')),
            ],
        ),
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_type', models.CharField(choices=[('DF', 'Default'), ('DG', 'Great'), ('DO', 'Ok'), ('DB', 'Bad')], default='DF', max_length=2)),
                ('session_id', models.CharField(max_length=255)),
                ('name', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cofounder.user')),
            ],
        ),
        migrations.CreateModel(
            name='ChatPromptParameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('prompt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parameters', to='cofounder.chatprompt')),
            ],
        ),
        migrations.CreateModel(
            name='ChatError',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error', models.TextField()),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cofounder.chatsession')),
            ],
        ),
        migrations.CreateModel(
            name='ChatCredit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credits', to='cofounder.chatsession')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credits', to='cofounder.user')),
            ],
        ),
    ]
