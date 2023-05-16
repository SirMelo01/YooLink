# Generated by Django 4.0.10 on 2023-05-16 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ycms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('email', models.CharField(max_length=60)),
                ('message', models.CharField(max_length=600)),
                ('date', models.DateField()),
                ('seen', models.BooleanField(default=False)),
            ],
        ),
    ]