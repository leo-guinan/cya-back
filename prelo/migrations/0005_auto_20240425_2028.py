# Generated by Django 3.2.25 on 2024-04-25 20:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0004_pitchdeckslide'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pitchdeck',
            name='status',
            field=models.CharField(choices=[('CR', 'Created'), ('UL', 'Uploaded'), ('PR', 'Processing'), ('RA', 'Ready for Analysis'), ('AN', 'Analyzing'), ('RR', 'Ready for Reporting'), ('RE', 'Reporting'), ('CP', 'Complete'), ('ER', 'Error')], default='CR', max_length=2),
        ),
        migrations.CreateModel(
            name='PitchDeckAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('compiled_slides', models.TextField()),
                ('initial_analysis', models.TextField(blank=True, null=True)),
                ('extra_analysis', models.TextField(blank=True, null=True)),
                ('report', models.TextField(blank=True, null=True)),
                ('deck', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analysis', to='prelo.pitchdeck')),
            ],
        ),
    ]