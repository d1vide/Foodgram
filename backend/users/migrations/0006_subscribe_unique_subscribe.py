# Generated by Django 3.2.3 on 2024-06-17 21:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20240618_0049'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='subscribe',
            constraint=models.UniqueConstraint(fields=('subscriber', 'user'), name='unique_subscribe'),
        ),
    ]
