import requests
from django.shortcuts import render
from django.contrib.auth.models import User, auth
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from bs4 import BeautifulSoup   
from django.contrib.auth.decorators import login_required
from .models import Account, Trade, ForexPair, OptionTrade
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from lxml import etree
import http.client
import decimal
from decimal import Decimal
from django.views.generic import View
import json
import random
from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
# Authentication Views 
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect('login')

    else:
        return render(request, 'login.html')

def register(request):


    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password==password2:       
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect(reverse('sign_up'))  # redirect to the sign up page using the reverse function
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect(reverse('sign_up'))  # redirect to the sign up page using the reverse function
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                demo_account = Account.objects.create(user=user, balance=1000.00, account_type='DEMO')
                demo_account.save()
                
                print('User Created')
                return redirect('login')

        else:
            messages.info(request, 'Password Not Matching')
            return redirect(reverse('sign_up'))  # redirect to the sign up page using the reverse function
        return redirect('/')

    else:
        return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('/')

# ... after processing the form data ...

# Project  views.

def index(request):
    user = request.user
    context = {'user': user}
    return render(request, 'index.html')

def get_forex_price(forex_pair):
    API_KEY = "e467de385980e930097f0386"  # Replace with your actual API key
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{forex_pair}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data.get("conversion_rate")
    else:
        print(f"Error: Failed to fetch {forex_pair} price. Status Code: {response.status_code}")
        return None

def get_trade_equity(trade):
    forex_pairs = ForexPair.objects.all()
    # Find the ForexPair object with a matching symbol to the trade's symbol
    matched_pair = None
    for forex_pair in forex_pairs:
        if trade.symbol == forex_pair.symbol:
            matched_pair = forex_pair
            break
    
    if matched_pair is None:
        print(f"Error: Could not find matching ForexPair for symbol {trade.symbol}")
        return None
    
    # Get the current price using the matched pair's pair
    current_price = get_forex_price(matched_pair.pair)
    current_price_decimal = Decimal(str(current_price))  # Convert to Decimal

    if current_price_decimal is not None:
        entry_price = Decimal(str(trade.entry))  # Convert to Decimal
        direction = trade.trade_direction
        lot_size = trade.lot_size
        
        if direction == 'BUY':
            equity = (current_price_decimal - entry_price) * lot_size * 1000
        elif direction == 'SELL':
            equity = (entry_price - current_price_decimal) * lot_size * 1000
        else:
            print(f"Error: Invalid trade direction {direction}")
            return None
        
        return equity
    else:
        print(f"Error: Could not fetch current price for {trade.symbol}")
        return None

@login_required
def TradingView(request):
    user = request.user
    forex_pairs = ForexPair.objects.all()

    forex_prices = {}
    trade_equity = {}
    total_equity = decimal.Decimal('0.0')
    trades = Trade.objects.filter(trader=user)

    for forex_pair in forex_pairs:
        price = get_forex_price(forex_pair.pair)
        if price:
            forex_prices[forex_pair] = price
            print(f"Pair: {forex_pair}, Price: {price}")


    for trade in trades:
        pair_symbol = trade.symbol

        for forex_pair in forex_pairs:
            if forex_pair.symbol == pair_symbol:
                matched_pair = forex_pair
                print(f"Symbol found {matched_pair}")
                
            else:
                print(f"Symbol is not found.")

        if matched_pair:
            current_price = get_forex_price(matched_pair)
            if current_price:
                equity = get_trade_equity(trade)
                trade_equity[trade] = equity
                total_equity += equity  # Add the equity to total equity
                trade.equity = equity
                trade.save()
                print(f"Trade {trade}, Equity {trade_equity[trade]}")
            else:
                print(f"No price found for symbol {pair_symbol}")
        else:
            print(f"Symbol Not found for trade {trade}")


    # Get the user's demo account balance
    default_price = get_forex_price('EUR/USD')
    print(f"Default price: {default_price}")
    demo_account = Account.objects.get(user=request.user, account_type='DEMO')
    demo_account_balance = demo_account.balance
    balance_equity = demo_account_balance + total_equity
    account_balance = 10000.00  # Retrieve user's account balance from the database
    open_positions = []  # Retrieve user's open positions from the database
    transaction_history = []  # Retrieve user's transaction history from the database

    context = {
        'trades': trades,
        'trade_equity': trade_equity,
        'total_equity': total_equity,
        'balance_equity': balance_equity,
        'forex_prices': forex_prices,
        'default_price': default_price,
        'account_balance': account_balance,
        'open_positions': open_positions,
        'transaction_history': transaction_history,
        'demo_account_balance': demo_account_balance,
        'user': user,
    }
    return render(request, 'trading.html', context)

def options(request, symbol):
    user = request.user
    pairs = ForexPair.objects.all()  # Default symbol
    demo_account = Account.objects.get(user=request.user, account_type='DEMO')
    demo_account_balance = demo_account.balance
    trades = OptionTrade.objects.filter(trader=user, expired=False).order_by('-id')
    all_trades = OptionTrade.objects.filter(trader=user).order_by('-id')
    closed_trades = OptionTrade.objects.filter(trader=user, expired=True).order_by('-id')[:5]

    try:
        forex_pair = ForexPair.objects.get(symbol=symbol)
        chart_data = forex_pair.chart_data
        # print(f"Chart Data for {symbol} is {chart_data}")
        
    except ForexPair.DoesNotExist:
        chart_data = []

    # Sample data
    my_list = [
        {"time": "2022-08-15", "value": 23951.689},
        {"time": "2022-08-16", "value": 24518.115},
        {"time": "2022-08-17", "value": 24790.088},
        {"time": "2022-08-18", "value": 25514.944},
        {"time": "2022-08-19", "value": 25312.807},
        {"time": "2022-08-22", "value": 21320.387}, 
        {"time": "2022-08-23", "value": 21374.044},
        {"time": "2022-08-24", "value": 21723.951},
        {"time": "2022-08-25", "value": 21619.032},
        {"time": "2022-08-26", "value": 20833.162},
        {"time": "2022-08-29", "value": 19987.848},
        {"time": "2022-08-30", "value": 20188.255},
        {"time": "2022-08-31", "value": 19827.705},
        {"time": "2022-09-01", "value": 20034.628},
        {"time": "2022-09-02", "value": 20074.527},
        {"time": "2022-09-05", "value": 19689.499},
        {"time": "2022-09-06", "value": 19462.254}, 
        {"time": "2022-09-07", "value": 1931.907},
        {"time": "2022-09-08", "value": 19603.278},
        {"time": "2022-09-09", "value": 20539.655},
        {"time": "2022-09-12", "value": 22016.156},
        {"time": "2022-09-13", "value": 21984.834},
        {"time": "2022-09-14", "value": 21283.414},
        {"time": "2022-09-15", "value": 20150.747},
        {"time": "2022-09-16", "value": 19746.438},
        {"time": "2022-09-19", "value": 19452.928},
        {"time": "2022-09-20", "value": 21180.027},
        {"time": "2022-09-21", "value": 20583.624},
        {"time": "2022-09-22", "value": 19296.092},
        {"time": "2022-09-23", "value": 19680.325},
        {"time": "2022-09-26", "value": 19409.023},
        {"time": "2022-09-27", "value": 19831.088},  
        {"time": "2022-09-28", "value": 19148.557},
        {"time": "2022-09-29", "value": 19695.746},
        {"time": "2022-09-30", "value": 19473.069},
        {"time": "2022-10-03", "value": 19905.457},
        {"time": "2022-10-04", "value": 20142.892},
        {"time": "2022-10-05", "value": 20297.638},
        {"time": "2022-10-06", "value": 20781.415}, 
        {"time": "2022-10-07", "value": 19717.127},
        {"time": "2022-10-10", "value": 19276.503},
        {"time": "2022-10-11", "value": 19380.639},
        {"time": "2022-10-12", "value": 19475.089},
        {"time": "2022-10-13", "value": 19576.598},
        {"time": "2022-10-14", "value": 19273.779},
        {"time": "2022-10-17", "value": 19285.034},
        {"time": "2022-10-18", "value": 19763.866},  
        {"time": "2022-10-19", "value": 20133.813},
        {"time": "2022-10-20", "value": 19177.090},
        {"time": "2022-10-21", "value": 19403.891},
        {"time": "2022-10-24", "value": 19361.227},
        {"time": "2022-10-25", "value": 20116.868},
        {"time": "2022-10-26", "value": 20274.393},
        {"time": "2022-10-27", "value": 20837.423},
        {"time": "2022-10-28", "value": 20641.007},
        {"time": "2022-10-31", "value": 20663.507},
        {"time": "2022-11-01", "value": 20505.410},
        {"time": "2022-11-02", "value": 20606.325}, 
        {"time": "2022-11-03", "value": 20189.865},
        {"time": "2022-11-04", "value": 21117.883},
        {"time": "2022-11-07", "value": 20782.424},
        {"time": "2022-11-08", "value": 17498.483},
        {"time": "2022-11-09", "value": 17599.766},
        {"time": "2022-11-10", "value": 17549.335},
        {"time": "2022-11-11", "value": 16870.088},
        {"time": "2022-11-14", "value": 16405.899},
        {"time": "2022-11-15", "value": 16767.073},
        {"time": "2022-11-16", "value": 16558.157},
        {"time": "2022-11-17", "value": 16675.582},
        {"time": "2022-11-18", "value": 16656.466},
        {"time": "2022-11-21", "value": 15938.690},
        {"time": "2022-11-22", "value": 16187.611},
        {"time": "2022-11-23", "value": 16479.129},
        {"time": "2022-11-24", "value": 16558.880},
        {"time": "2022-11-25", "value": 16397.618},
        {"time": "2022-11-28", "value": 16269.528},
        {"time": "2022-11-29", "value": 16737.025},
        {"time": "2022-11-30", "value": 16868.811},
        {"time": "2022-12-01", "value": 16973.513},
        {"time": "2022-12-02", "value": 16918.993},
        {"time": "2022-12-05", "value": 17016.476},
        {"time": "2022-12-06", "value": 17131.437},
        {"time": "2022-12-07", "value": 16982.363},
        {"time": "2022-12-08", "value": 17210.353},
        {"time": "2022-12-09", "value": 17179.253},
        {"time": "2022-12-12", "value": 16990.087},
        {"time": "2022-12-13", "value": 16834.525},
        {"time": "2022-12-14", "value": 16816.774},
        {"time": "2022-12-15", "value": 16780.174},
        {"time": "2022-12-16", "value": 16760.656},
        {"time": "2022-12-19", "value": 16734.929},
        {"time": "2022-12-20", "value": 16702.687},
        {"time": "2022-12-21", "value": 16643.839},
        {"time": "2022-12-22", "value": 16785.660},
        {"time": "2022-12-23", "value": 16737.472},
        {"time": "2022-12-26", "value": 16751.407},
        {"time": "2022-12-27", "value": 16737.585},
        {"time": "2022-12-28", "value": 16435.590},
        {"time": "2022-12-29", "value": 16556.311},
        {"time": "2022-12-30", "value": 16545.395},
        {"time": "2023-01-02", "value": 16765.959},
        {"time": "2023-01-03", "value": 16884.159},
        {"time": "2023-01-04", "value": 17200.393},
        {"time": "2023-01-05", "value": 17363.207},
        {"time": "2023-01-06", "value": 17485.702},
        {"time": "2023-01-09", "value": 17202.969},
        {"time": "2023-01-10", "value": 17399.425},
        {"time": "2023-01-11", "value": 17448.263},
        {"time": "2023-01-12", "value": 17536.846},
        {"time": "2023-01-13", "value": 17667.679},
        {"time": "2023-01-16", "value": 17606.949},
        {"time": "2023-01-17", "value": 17111.453},
        {"time": "2023-01-18", "value": 17244.829},
        {"time": "2023-01-19", "value": 17076.611},
        {"time": "2023-01-20", "value": 17611.565},
        {"time": "2023-01-23", "value": 17927.033},
        {"time": "2023-01-24", "value": 22852.017},
        {"time": "2023-01-25", "value": 23616.204},
        {"time": "2023-01-26", "value": 23356.152},
        {"time": "2023-01-27", "value": 22981.801},
        {"time": "2023-01-30", "value": 23284.279},
        {"time": "2023-01-31", "value": 23186.377},
        {"time": "2023-02-01", "value": 22902.148},
        {"time": "2023-02-02", "value": 23021.817}, 
        {"time": "2023-02-03", "value": 22973.412},
        {"time": "2023-02-06", "value": 22942.542},
        {"time": "2023-02-07", "value": 22938.235},
        {"time": "2023-02-08", "value": 22500.270},
        {"time": "2023-02-09", "value": 21881.302},
        {"time": "2023-02-10", "value": 21739.171},
        {"time": "2023-02-13", "value": 21577.951},
        {"time": "2023-02-14", "value": 21947.072},
        {"time": "2023-02-15", "value": 22372.267},
        {"time": "2023-02-16", "value": 24189.773},
        {"time": "2023-02-17", "value": 24656.677},
        {"time": "2023-02-20", "value": 24628.192},
        {"time": "2023-02-21", "value": 24565.924},
        {"time": "2023-02-22", "value": 24148.981},
        {"time": "2023-02-23", "value": 23510.192},
        {"time": "2023-02-24", "value": 23615.780},
        {"time": "2023-02-27", "value": 23255.670},
        {"time": "2023-02-28", "value": 23291.044},
        {"time": "2023-03-01", "value": 23605.451},
        {"time": "2023-03-02", "value": 23544.295},
        {"time": "2023-03-03", "value": 22787.194},
        {"time": "2023-03-06", "value": 22956.234},
        {"time": "2023-03-07", "value": 22984.559},
        {"time": "2023-03-08", "value": 22654.729},
        {"time": "2023-03-09", "value": 22873.194},
        {"time": "2023-03-10", "value": 22999.037},
        {"time": "2023-03-13", "value": 21496.076},
        {"time": "2023-03-14", "value": 21763.488},
        {"time": "2023-03-15", "value": 21576.658},
        {"time": "2023-03-16", "value": 21637.887},
        {"time": "2023-03-17", "value": 21219.286},
        {"time": "2023-03-20", "value": 22090.824},
        {"time": "2023-03-21", "value": 22306.930},
        {"time": "2023-03-22", "value": 22426.450},
        {"time": "2023-03-23", "value": 22475.408},
        {"time": "2023-03-24", "value": 24412.709},
        {"time": "2023-03-27", "value": 24791.040},
        {"time": "2023-03-28", "value": 24223.563},
        {"time": "2023-03-29", "value": 24150.437},
        {"time": "2023-03-30", "value": 23867.308},
        {"time": "2023-03-31", "value": 23832.118},
        {"time": "2023-04-03", "value": 23742.124},
        {"time": "2023-04-04", "value": 23030.771},
        {"time": "2023-04-05", "value": 23016.497},
        {"time": "2023-04-06", "value": 22488.677},
        {"time": "2023-04-07", "value": 22565.950},
        {"time": "2023-04-10", "value": 23431.984},
        {"time": "2023-04-11", "value": 24066.160},
        {"time": "2023-04-12", "value": 24372.498},
        {"time": "2023-04-13", "value": 24666.296},
        {"time": "2023-04-14", "value": 25241.633},
        {"time": "2023-04-17", "value": 25298.721},
        {"time": "2023-04-18", "value": 25891.466},
        {"time": "2023-04-19", "value": 25278.671},
        {"time": "2023-04-20", "value": 25199.740},
        {"time": "2023-04-21", "value": 25299.770},
        {"time": "2023-04-24", "value": 25399.605},
        {"time": "2023-04-25", "value": 25607.194},
        {"time": "2023-04-26", "value": 25142.585},
        {"time": "2023-04-27", "value": 24861.884},
        {"time": "2023-04-28", "value": 24826.568},
        {"time": "2023-05-02", "value": 24919.559},
        {"time": "2023-05-03", "value": 25209.602},
        {"time": "2023-05-04", "value": 25525.770},
        {"time": "2023-05-05", "value": 25955.857},
        {"time": "2023-05-08", "value": 25726.806},
        {"time": "2023-05-09", "value": 25406.947},
        {"time": "2023-05-10", "value": 24912.425},
        {"time": "2023-05-11", "value": 24618.294},
        {"time": "2023-05-12", "value": 23779.273},
        {"time": "2023-05-15", "value": 23165.672},
        {"time": "2023-05-16", "value": 22962.143},
        {"time": "2023-05-17", "value": 22375.114},
        {"time": "2023-05-18", "value": 22325.137},
        {"time": "2023-05-19", "value": 21706.670},
        {"time": "2023-05-22", "value": 21709.729},
        {"time": "2023-05-23", "value": 21655.152},
        {"time": "2023-05-24", "value": 20885.636},
        {"time": "2023-05-25", "value": 20940.629},
        {"time": "2023-05-26", "value": 21268.321},
        {"time": "2023-05-29", "value": 20753.901},
        {"time": "2023-05-30", "value": 20794.660},
        {"time": "2023-05-31", "value": 20310.181},
        {"time": "2023-06-01", "value": 20298.529},
    ]
    
    # Only update if chart_data is empty
    if not chart_data:
        forex_pair, created = ForexPair.objects.update_or_create(
            symbol=symbol,
            defaults={'chart_data': my_list}
        )
        chart_data_to_use = my_list
    else:
        chart_data_to_use = chart_data

    context = {
        'chart_data': json.dumps(chart_data_to_use),
        'pairs': pairs,
        'trades': trades,
        'all_trades': all_trades,
        'closed_trades': closed_trades,
        'symbol': symbol,
        'demo_account_balance': demo_account_balance
    }

    return render(request, 'options.html', context)

def update_new_data(request):
    user = request.user  # Make sure to retrieve the user
    demo_account = Account.objects.get(user=request.user, account_type='DEMO')
    demo_account_balance = demo_account.balance
    trades = OptionTrade.objects.filter(trader=user).order_by('-id')

    new_data = {
        'trades': trades,
        'demo_account_balance': demo_account_balance,
    }
    return JsonResponse(new_data)
    

def dashboard(request):
    return render(request, 'dashboard')

def selected_pair(request, currency_pair):
    user = request.user
    pairs = ForexPair.objects.all()
    # Existing code...
    forex_pairs = ForexPair.objects.all()
    forex_prices = {}
    trades = Trade.objects.filter(trader=user)

    for forex_pair in forex_pairs:
        price = get_forex_price(forex_pair.pair)
        if price:
            forex_prices[forex_pair] = price
            print(f"Pair: {forex_pair}, Price: {price}")

    currency = ForexPair.objects.get(symbol=currency_pair)
    print(f"Currency: {currency.pair}")


    # Get the user's demo account balance
    demo_account = Account.objects.get(user=request.user, account_type='DEMO')
    demo_account_balance = demo_account.balance

    account_balance = 10000.00  # Retrieve user's account balance from the database
    open_positions = []  # Retrieve user's open positions from the database
    transaction_history = []  # Retrieve user's transaction history from the database
    pair_price = get_forex_price(currency.pair)

    print(f"Currency Pair: {currency_pair}, Price: {pair_price}")
    context = {
        'currency_pair': currency_pair,
        'trades': trades,
        'pair_price': pair_price,
        'forex_prices': forex_prices,
        'price': price,
        'account_balance': account_balance,
        'open_positions': open_positions,
        'transaction_history': transaction_history,
        'demo_account_balance': demo_account_balance,
        'user': user,
    }
    return render(request, 'trading.html', context)


def place_trade(request, direction):
    user = request.user
    if request.method == 'POST':
        # Get the take profit, stop loss, and lot size from the form submission
        take_profit = request.POST.get('take_profit')
        stop_loss = request.POST.get('stop_loss')
        entry = request.POST.get('entry')
        lot_size = request.POST.get('lot_size')
        symbol = request.POST.get('symbol')

        
        # Save the trade details to the database
        trade = Trade.objects.create(
            trader=user,
            trade_direction=direction,
            entry=entry,
            take_profit=take_profit,
            stop_loss=stop_loss,
            lot_size=lot_size,
            symbol=symbol
        )

        # Pass the scraped symbol and other trade details to the template
        context = {
            'direction': direction,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'lot_size': lot_size,
            'symbol': symbol,
        }

        return render(request, 'trade_success.html', context)

    # If the request method is not POST, render the form page
    return render(request, 'place_trade_form.html')

# views.py

def place_option_trade(request, option_type):
    user = request.user
    demo_account = Account.objects.get(user=request.user, account_type='DEMO')
    demo_account_balance = demo_account.balance
    
    if request.method == 'POST':

        symbol = request.POST.get('symbol')
        stake = request.POST.get('stake')
        expiration = request.POST.get('expiration')
        pair = get_object_or_404(ForexPair, symbol=symbol)
        chart_data = pair.chart_data

        last_point = chart_data[-1]
        strike_price = last_point['value']
        strike_time = last_point['time']

        demo_account_balance = demo_account.balance - Decimal(stake)
        demo_account.balance = demo_account_balance
        demo_account.save()

        expire_days = int(expiration) * 30
        expire_time = datetime.strptime(last_point['time'], '%Y-%m-%d') + timedelta(days=expire_days)
        print(f"{option_type} {symbol} at {strike_price} during {strike_time} to expire at {expire_time}")

        option = OptionTrade.objects.create(
            trader=user,
            symbol = symbol,
            expiration = expiration,
            strike_price = strike_price,
            option_type = option_type,
            stake = stake,
            close_time=expire_time
        )
    
        strike_price = option.strike_price  
        print(f"strike price {strike_price}")
        return JsonResponse({'strike_price': strike_price})
    else:
        # Invalid request
        return HttpResponseBadRequest()
    
def update_trade_outcomes(request):
    now = timezone.now()
    user = request.user
    demo_account = Account.objects.get(user=request.user, account_type='DEMO')
    demo_account_balance = demo_account.balance
    trades = OptionTrade.objects.filter(trader=user, expired=False)

    for trade in trades:
        print(f"Checking trade outcome for {trade}. ")
        try:
            forex_pair = ForexPair.objects.get(symbol=trade.symbol)
            closing_time = trade.close_time

            closing_date = closing_time.date()  # Extract the date part

            if closing_date in [datetime.strptime(point['time'], '%Y-%m-%d').date() for point in forex_pair.chart_data]:
                # Find the corresponding closing price
                closing_price = next(point['value'] for point in forex_pair.chart_data if datetime.strptime(point['time'], '%Y-%m-%d').date() == closing_date)

                trade.closing_price = closing_price
                trade.save()

                outcome = trade.calculate_outcome()
                trade.outcome = outcome
                trade.expired = True
                trade.save()
                print(f"trade outcome for {trade.symbol} updated")
                print(f" Outcome is {outcome} ")

                # Update demo account balance based on trade outcome
                if outcome == 'won':
                    stake_multiplier = 2  # Multiplier for the stake
                    stake = Decimal(trade.stake) * stake_multiplier

                    demo_account_balance = demo_account.balance + stake
                    demo_account.balance = demo_account_balance
                    demo_account.save()

                    # Mark the trade as expired after updating the balance
                    
                    trade.save()
                    print(f"Demo account balance updated: {demo_account_balance}")
            else:
                print(f"Closing time not found")
        except ForexPair.DoesNotExist:
            print(f"ForexPair Doesn't exist")
            pass

    return HttpResponse("Trade outcomes updated.")

class OptionsView(View):
    def post(self, request):
        user = request.user

        trade_type = request.data['trade_type'] 
        symbol = request.data['symbol']
        strike_price = request.data['strike_price']
        expiry_date = request.data['expiry_date']

        trade = Trade.objects.create(
        user=user,
        trade_type=trade_type,
        symbol=symbol, 
        strike_price=strike_price,
        expiry_date=expiry_date
        )

        # Emit trade via websocket

        return JsonResponse({'status': 'created'})

def chart_view(request):
    symbol = 'LIONTC'  # Default symbol

    try:
        forex_pair = ForexPair.objects.get(symbol=symbol)
        chart_data = json.loads(forex_pair.chart_data)
    except ForexPair.DoesNotExist:
        chart_data = []

    context = {
        'chart_data': json.dumps(chart_data)
    }

    return render(request, 'charts.html', context)

def live_chart(request):
    return render(request, 'live_charts.html',)
    


def update_chart_data(request, symbol):


    try:
        pair = ForexPair.objects.get(symbol=symbol)

    except ForexPair.DoesNotExist:
        return JsonResponse({'error': 'Invalid symbol'})
    
    if symbol == 'LIONTC':

        # Get existing data 
        data = pair.chart_data 

        # Generate new point
        last_point = data[-1]
        next_time = datetime.strptime(last_point['time'], '%Y-%m-%d') + timedelta(days=1)
        next_value = last_point['value'] + (random.random() - 0.5) * 5

        new_point = {
        'time': next_time.strftime('%Y-%m-%d'),
        'value': next_value
        }

        # Append new point
        data.append(new_point)

        # Save updated data
        pair.chart_data = data
        pair.save()

        return JsonResponse(new_point)

    else:
        return JsonResponse({'error': 'Invalid symbol'})

class ChartDataView(View):
    def get(self, request):
        symbol = request.GET.get('symbol')

        # Get chart data

        data = {
        'labels': [],
        'datasets': [
            {
            'label': symbol,
            'data': [] 
            }
        ]
        }

        return JsonResponse(data)






@login_required
def account_dashboard(request):
    user = request.user
    try:
        account = Account.objects.get(user=user)
    except Account.DoesNotExist:
        account = None

    context = {
        'account': account
    }

    return render(request, 'account_dashboard.html', context)