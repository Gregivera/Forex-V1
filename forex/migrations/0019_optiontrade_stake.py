# Generated by Django 3.2.16 on 2023-08-24 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forex', '0018_remove_optiontrade_stake'),
    ]

    operations = [
        migrations.AddField(
            model_name='optiontrade',
            name='stake',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
