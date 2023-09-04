# models.py

from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField


class Account(models.Model):
    ACCOUNT_TYPES = (
        ('DEMO', 'Demo Account'),
        ('LIVE', 'Live Account'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=4, choices=ACCOUNT_TYPES, default='DEMO')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Add any other account-related fields here

    def __str__(self):
        return f"{self.user.username} - {self.get_account_type_display()} Account"

class ForexPair(models.Model):
    symbol = models.CharField(max_length=10, null=True, blank=True, default="LIONTC")
    pair = models.CharField(max_length=100, null=True, blank=True)
    chart_data = JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return self.symbol

class OptionTrade(models.Model):
    trader = models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    stake = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiration = models.PositiveSmallIntegerField()
    option_type = models.CharField(max_length=4)  
    strike_price = models.DecimalField(max_digits=10, decimal_places=2)
    closing_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    open_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    close_time = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(max_length=4, null=True, blank=True)
    expired = models.BooleanField(default=False)

    def calculate_outcome(self):
        if self.option_type == 'CALL':
            if self.closing_price > self.strike_price:
                return 'won'
            else:
                return 'lost'
        elif self.option_type == 'PUT':
            if self.closing_price < self.strike_price:
                return 'won'
            else:
                return 'lost'


class Trade(models.Model):
    DIRECTION_CHOICES = [('BUY', 'Buy'), ('SELL', 'Sell')]
    trader = models.ForeignKey(User, on_delete=models.CASCADE)
    trade_direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    entry = models.DecimalField(max_digits=10, decimal_places=4, default=False)
    take_profit = models.DecimalField(max_digits=10, decimal_places=4)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=4)
    lot_size = models.DecimalField(max_digits=10, decimal_places=2)
    equity = models.DecimalField(max_digits=10, decimal_places=2, default=False)
    symbol = models.CharField(max_length=7)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def close_trade(self):
        self.closed_at = timezone.now()
        self.is_active = False
        self.save()

    def __str__(self):
        return f"{self.trade_direction} {self.lot_size} lots of {self.symbol}"
