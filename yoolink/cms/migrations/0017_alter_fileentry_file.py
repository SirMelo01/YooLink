# Generated by Django 4.0.10 on 2023-04-06 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0016_alter_fileentry_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fileentry',
            name='file',
            field=models.FileField(upload_to='media'),
        ),
    ]