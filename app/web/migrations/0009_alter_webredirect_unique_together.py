# Generated by Django 3.2.3 on 2021-06-03 04:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0008_webredirect'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='webredirect',
            unique_together={('source_path', 'destination_path')},
        ),
    ]
