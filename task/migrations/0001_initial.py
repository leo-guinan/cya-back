# Generated by Django 3.2.24 on 2024-03-06 16:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024)),
                ('url', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scope', models.CharField(choices=[('PR', 'Private'), ('PB', 'Public'), ('LM', 'Limited')], default='PR', max_length=2)),
                ('task', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.CharField(max_length=255, unique=True)),
                ('details', models.TextField()),
                ('taskFor', models.TextField()),
                ('complete', models.BooleanField(default=False)),
                ('completedAt', models.DateTimeField(blank=True, null=True)),
                ('user_id', models.TextField()),
                ('parent', models.ForeignKey(blank=True, db_column='parent', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='children', to='task.task')),
            ],
        ),
    ]
