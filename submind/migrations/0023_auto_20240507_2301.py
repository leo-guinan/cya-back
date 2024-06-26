# Generated by Django 3.2.25 on 2024-05-07 23:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('submind', '0022_auto_20240507_2211'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='initiated_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='initiated_conversations', to='submind.submind'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='conversation',
            name='participants',
            field=models.ManyToManyField(related_name='conversations', to='submind.Submind'),
        ),
    ]
