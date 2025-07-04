# Generated by Django 4.0.10 on 2025-05-12 18:54

from django.db import migrations, models
import yoolink.ycms.models


class Migration(migrations.Migration):

    dependencies = [
        ('ycms', '0043_anyfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='favicon',
            field=models.ImageField(blank=True, default='', upload_to=yoolink.ycms.models.upload_to_user_settings),
        ),
        migrations.AddField(
            model_name='usersettings',
            name='logo',
            field=models.ImageField(blank=True, default='', upload_to=yoolink.ycms.models.upload_to_user_settings),
        ),
    ]
