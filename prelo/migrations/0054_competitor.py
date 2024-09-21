# Generated by Django 3.2.25 on 2024-09-15 17:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0053_sourcedeckupload'),
    ]

    operations = [
        migrations.CreateModel(
            name='Competitor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('description', models.TextField()),
                ('competitor_report', models.TextField()),
                ('funding_report', models.TextField()),
                ('benefit_report', models.TextField()),
                ('price_report', models.TextField()),
                ('market_share_report', models.TextField()),
                ('deck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competitors', to='prelo.pitchdeck')),
            ],
        ),
    ]