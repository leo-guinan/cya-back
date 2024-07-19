# Generated by Django 3.2.25 on 2024-05-18 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0021_auto_20240513_1506'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='investor',
            name='firm',
        ),
        migrations.CreateModel(
            name='InvestmentFirm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thesis', models.TextField()),
                ('investors', models.ManyToManyField(related_name='firms', to='prelo.Investor')),
                ('portfolio_companies', models.ManyToManyField(related_name='investors', to='prelo.Company')),
            ],
        ),
    ]