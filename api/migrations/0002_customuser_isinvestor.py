# Generated by Django 4.2.13 on 2024-08-13 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='isInvestor',
            field=models.BooleanField(default=False),
        ),
    ]
