# Generated by Django 4.0.10 on 2023-03-19 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0004_delete_galerie'),
    ]

    operations = [
        migrations.CreateModel(
            name='Galerie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='files')),
            ],
        ),
    ]