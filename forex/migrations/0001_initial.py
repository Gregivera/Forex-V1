# Generated by Django 3.2.16 on 2023-08-18 06:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ForexPair',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(blank=True, max_length=10, null=True)),
                ('pair', models.CharField(blank=True, max_length=100, null=True)),
                ('chart_data', models.CharField(default='[]', max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='TradeOptions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=10)),
                ('trade_type', models.CharField(choices=[('CALL', 'Call'), ('PUT', 'Put')], max_length=4)),
                ('strike_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('expiry_date', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trade_direction', models.CharField(choices=[('BUY', 'Buy'), ('SELL', 'Sell')], max_length=4)),
                ('entry', models.DecimalField(decimal_places=4, default=False, max_digits=10)),
                ('take_profit', models.DecimalField(decimal_places=4, max_digits=10)),
                ('stop_loss', models.DecimalField(decimal_places=4, max_digits=10)),
                ('lot_size', models.DecimalField(decimal_places=2, max_digits=10)),
                ('equity', models.DecimalField(decimal_places=2, default=False, max_digits=10)),
                ('symbol', models.CharField(max_length=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('trader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_type', models.CharField(choices=[('DEMO', 'Demo Account'), ('LIVE', 'Live Account')], default='DEMO', max_length=4)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]