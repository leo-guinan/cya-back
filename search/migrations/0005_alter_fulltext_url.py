# Generated by Django 3.2.18 on 2023-04-02 18:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0004_alter_recommendation_affiliate_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fulltext',
            name='url',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fulltexts', to='search.link'),
        ),
    ]
