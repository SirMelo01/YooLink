# Generated by Django 4.0.10 on 2025-04-13 14:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ycms', '0041_button_hover_text_de_button_hover_text_en_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pricingcard',
            name='monthly_price_de',
        ),
        migrations.RemoveField(
            model_name='pricingcard',
            name='monthly_price_en',
        ),
        migrations.RemoveField(
            model_name='pricingcard',
            name='one_time_price_de',
        ),
        migrations.RemoveField(
            model_name='pricingcard',
            name='one_time_price_en',
        ),
    ]
