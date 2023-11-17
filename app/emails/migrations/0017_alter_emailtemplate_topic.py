# Generated by Django 4.0.10 on 2023-11-16 23:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emails', '0016_shorten_message_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailtemplate',
            name='topic',
            field=models.CharField(choices=[('GENERAL', 'General'), ('REPAIRS', 'Repairs'), ('BONDS', 'Bonds'), ('EVICTION', 'Eviction'), ('HEALTH_CHECK', 'Housing Health Check'), ('RENT_REDUCTION', 'Rent reduction'), ('OTHER', 'Other')], max_length=32),
        ),
    ]
