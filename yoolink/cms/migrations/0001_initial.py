# Generated by Django 4.0.10 on 2023-03-18 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Text_Content',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text1', models.CharField(max_length=1000, null=True)),
                ('text2', models.CharField(max_length=1000, null=True)),
            ],
        ),
    ]