# Generated by Django 4.0.10 on 2023-07-29 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ycms', '0004_blog_code_blog_last_updated_blog_slug_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='fileentry',
            name='title',
            field=models.CharField(default='Bildtitel', max_length=200),
        ),
        migrations.AddField(
            model_name='galeryimage',
            name='title',
            field=models.CharField(default='Bildtitel', max_length=200),
        ),
    ]