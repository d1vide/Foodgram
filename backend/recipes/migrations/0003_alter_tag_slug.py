# Generated by Django 3.2.3 on 2024-06-23 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20240623_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(max_length=32, unique=True, verbose_name='Идентификатор'),
        ),
    ]
