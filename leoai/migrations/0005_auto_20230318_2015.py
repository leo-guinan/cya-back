# Generated by Django 3.2.18 on 2023-03-18 20:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leoai', '0004_auto_20230318_1529'),
    ]

    operations = [
        migrations.CreateModel(
            name='Facts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterField(
            model_name='item',
            name='collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='leoai.collection'),
        ),
        migrations.CreateModel(
            name='FactItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.TextField()),
                ('fact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='leoai.facts')),
            ],
        ),
    ]
