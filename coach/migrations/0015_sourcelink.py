# Generated by Django 3.2.20 on 2023-09-12 23:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coach', '0014_source'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourceLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=255, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='coach.source')),
            ],
        ),
    ]
