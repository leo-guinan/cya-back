# Generated by Django 3.2.25 on 2024-05-02 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submind', '0012_alter_submind_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='supporting_data',
            field=models.TextField(blank=True, null=True),
        ),
    ]