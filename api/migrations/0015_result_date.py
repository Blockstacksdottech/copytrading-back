# Generated by Django 4.2.13 on 2024-09-04 15:44

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_result_todays_pl_alter_customuser_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='date',
            field=models.DateField(default=datetime.datetime(2024, 9, 4, 15, 44, 28, 194139, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
    ]
