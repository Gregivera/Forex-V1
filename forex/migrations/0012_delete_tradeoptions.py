# Generated by Django 3.2.16 on 2023-08-24 15:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forex', '0011_optiontrade_expired'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TradeOptions',
        ),
    ]
