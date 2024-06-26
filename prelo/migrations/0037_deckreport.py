# Generated by Django 3.2.25 on 2024-06-13 16:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0036_auto_20240612_0045'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeckReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('s3_path', models.CharField(max_length=255)),
                ('deck', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='report', to='prelo.pitchdeck')),
            ],
        ),
    ]
