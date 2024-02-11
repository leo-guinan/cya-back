# Generated by Django 3.2.23 on 2024-02-09 15:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cofounder', '0008_command'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.CharField(max_length=255, unique=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cofounder.chatsession')),
            ],
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('question', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.CharField(max_length=255, unique=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cofounder.chatsession')),
            ],
        ),
    ]