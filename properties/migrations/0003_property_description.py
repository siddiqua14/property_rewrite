# Generated by Django 4.2.17 on 2024-12-30 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0002_remove_property_hotel_id_remove_property_title_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='description',
            field=models.TextField(default='Not rewritten'),
        ),
    ]