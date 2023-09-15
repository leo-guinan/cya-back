# Generated by Django 3.2.20 on 2023-09-15 19:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uploaded_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='experiments.uploadedfile')),
            ],
        ),
        migrations.CreateModel(
            name='ExperimentResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.TextField()),
                ('variant', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='experiments.experimentmessage')),
                ('uploaded_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='experiments.uploadedfile')),
            ],
        ),
    ]
