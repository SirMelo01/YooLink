# Generated by Django 4.0.10 on 2023-04-25 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_blog_title_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='title_image',
            field=models.ImageField(blank=True, default='', upload_to='yoolink/'),
        ),
    ]