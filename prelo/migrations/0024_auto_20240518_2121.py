# Generated by Django 3.2.25 on 2024-05-18 21:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0023_auto_20240518_2015'),
    ]

    operations = [
        migrations.RenameField(
            model_name='investorreport',
            old_name='thesis_reasons',
            new_name='recommendation_reasons',
        ),
        migrations.RemoveField(
            model_name='investorreport',
            name='thesis_match_score',
        ),
        migrations.AddField(
            model_name='investorreport',
            name='firm',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='prelo.investmentfirm'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='investorreport',
            name='investment_potential_score',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pitchdeckanalysis',
            name='investor_report',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='analysis', to='prelo.investorreport'),
        ),
    ]
