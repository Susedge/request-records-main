# Generated by Django 5.1.6 on 2025-04-27 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinerequest', '0008_user_request_approved_requirements'),
    ]

    operations = [
        migrations.AddField(
            model_name='user_request',
            name='approved',
            field=models.BooleanField(default=False),
        ),
    ]
