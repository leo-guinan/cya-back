# Generated by Django 3.2.25 on 2024-04-25 16:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0003_alter_pitchdeck_uuid'),
    ]

    operations = [
        migrations.CreateModel(
            name='PitchDeckSlide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('order', models.IntegerField()),
                ('s3_path', models.CharField(blank=True, max_length=255, null=True)),
                ('category', models.CharField(blank=True, max_length=255, null=True)),
                ('uuid', models.CharField(max_length=255, unique=True)),
                ('deck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slides', to='prelo.pitchdeck')),
            ],
        ),
    ]