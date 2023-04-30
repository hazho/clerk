# Generated by Django 4.0.9 on 2023-04-30 01:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_person_support_contact_preferences'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='topic',
            field=models.CharField(choices=[('HEALTH_CHECK', 'Housing Health Check'), ('REPAIRS', 'Repairs'), ('BONDS', 'Bonds'), ('RENT_REDUCTION', 'Rent reduction'), ('EVICTION', 'Eviction'), ('OTHER', 'Other')], max_length=32),
        ),
    ]
