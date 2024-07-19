# Generated by Django 3.2.25 on 2024-06-04 18:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prelo', '0028_pitchdeck_user_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='DealMemo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memo', models.TextField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='investor_memos', to='prelo.company')),
                ('firm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memos', to='prelo.investmentfirm')),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memos', to='prelo.investor')),
            ],
        ),
    ]