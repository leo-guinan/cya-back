# Generated by Django 3.2.25 on 2024-07-12 17:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0043_pitchdeckanalysis_founder_contact_info'),
    ]

    operations = [
        migrations.CreateModel(
            name='RejectionEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deck_uuid', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('email', models.CharField(max_length=255)),
                ('subject', models.CharField(max_length=255)),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rejections', to='prelo.investor')),
            ],
        ),
    ]
