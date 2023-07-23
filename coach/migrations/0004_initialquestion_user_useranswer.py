# Generated by Django 3.2.19 on 2023-07-22 16:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('coach', '0003_delete_messagestore'),
    ]

    operations = [
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
            name='UserAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.CharField(max_length=255)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='coach.initialquestion')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='coach.user')),
            ],
        ),
    ]
