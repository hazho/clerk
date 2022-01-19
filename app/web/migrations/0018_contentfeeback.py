# Generated by Django 3.2.10 on 2022-01-19 04:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0066_collection_management_permissions'),
        ('web', '0017_auto_20220119_1523'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentFeeback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(choices=[(1, '⭐'), (2, '⭐⭐'), (3, '⭐⭐⭐'), (4, '⭐⭐⭐⭐'), (5, '⭐⭐⭐⭐⭐')])),
                ('reason', models.CharField(blank=True, default='', max_length=2048)),
                ('name', models.CharField(blank=True, default='', max_length=32)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.page')),
            ],
        ),
    ]
