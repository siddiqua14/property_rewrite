# Generated by Django 4.2.17 on 2024-12-30 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hotel_id', models.IntegerField(unique=True)),
                ('title', models.CharField(max_length=255)),
            ],
        ),
    ]
