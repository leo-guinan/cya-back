# Generated by Django 3.2.20 on 2023-09-02 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coach', '0010_auto_20230812_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='chat_type',
            field=models.CharField(choices=[('DF', 'Default'), ('DG', 'Great'), ('DO', 'Ok'), ('DB', 'Bad')], default='DF', max_length=2),
        ),
    ]
