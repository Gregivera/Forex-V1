"""lionfx URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from forex import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('trading/', views.TradingView, name='trading'),
    path('options_trading/<str:symbol>/', views.options, name='options'),
    path('trade_options/<str:option_type>/', views.place_option_trade, name='place_option_trade'),
    path('update_trade_outcomes/', views.update_trade_outcomes, name='update_trade_outcomes'),
    path('update_new_data/', views.update_new_data, name='update_new_data'),
    path('update_chart_data/<str:symbol>/', views.update_chart_data, name='update_chart_data'),
    path('pair/<str:currency_pair>/', views.selected_pair, name='selected_pair'),
    path('place_trade/<str:direction>/', views.place_trade, name='place_trade'),
    path('accounts/login/', views.login, name='login'),
    path('accounts/logout/', views.logout, name='logout'),
    path('accounts/signup/', views.register, name='sign_up')
]
