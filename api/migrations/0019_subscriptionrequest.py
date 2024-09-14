# Generated by Django 4.2.13 on 2024-09-14 14:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_recoveryrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('approved', models.BooleanField(default=False)),
                ('date_requested', models.DateTimeField(auto_now_add=True)),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.strategy')),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
