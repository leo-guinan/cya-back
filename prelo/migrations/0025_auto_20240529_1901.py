# Generated by Django 3.2.25 on 2024-05-29 19:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0024_auto_20240518_2121'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='deck',
        ),
        migrations.AddField(
            model_name='pitchdeck',
            name='company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='decks', to='prelo.company'),
        ),
        migrations.AddField(
            model_name='pitchdeck',
            name='version',
            field=models.IntegerField(default=1),
        ),
        migrations.CreateModel(
            name='UpdatedVersionAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('risks_addressed', models.TextField(blank=True, null=True)),
                ('slides_changed', models.TextField(blank=True, null=True)),
                ('questions_answered', models.TextField(blank=True, null=True)),
                ('still_missing', models.TextField(blank=True, null=True)),
                ('new_deck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='new_version', to='prelo.pitchdeck')),
                ('previous_deck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='previous_version', to='prelo.pitchdeck')),
            ],
        ),
    ]
