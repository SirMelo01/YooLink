# Generated by Django 4.0.10 on 2023-03-19 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0002_text_content_bild'),
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