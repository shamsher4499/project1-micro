import requests
from django.shortcuts import render, redirect
import stripe
from django.conf import settings
from dataclasses import dataclass
from api.dwolla_payment import DwollaSubscriptionAPI
from superadmin.models import UserSubscription, LenderWallet, SubscriptionPlan
from datetime import datetime, timedelta
from .email import subscriptionSucess, subscriptionReject

docs_type = ['pdf', 'jpg', 'jpeg', 'png', 'docs', 'xls', 'csv']

stripe.api_key = settings.STRIPE_SECRET_KEY

def get_size(file):
    return file.size <= 5*1048576

def check_superuser(user):
    if user.is_superuser:
        return True
    else:
        return False

def check_user_type(func=None):
    def wrapper(request):
        if not request.user.is_superuser:
            return redirect('home')
        # return redirect(request.path)
    return wrapper

def get_ip():
    try:
        session_data = requests.Session()
        response = session_data.get('https://api64.ipify.org?format=json').json()
        return response["ip"]
    except:
        return None

def get_location(ip_address):
    session_data = requests.Session()
    response = session_data.get(f'https://ipapi.co/{ip_address}/json/').json()
    location_data = {
        "ip": ip_address,
        "city": response.get("city"),
        "region": response.get("region"),
        "country": response.get("country_name")
    }
    return location_data

    
def check_user_count():
    return UserSubscription.objects.filter(current_period_end__lte=datetime.now()).exists()

def checkout_subscriptions():
    if check_user_count():
        plan_price = SubscriptionPlan.objects.get(name='Premium Plan')
        all_users = UserSubscription.objects.filter(current_period_end__lte=datetime.now())
        all_user_wallet = LenderWallet.objects.filter(user_id__in=all_users.values_list('user_id', flat=True))
        success_user = []
        for i in all_user_wallet:
            status = DwollaSubscriptionAPI.create_subscription(i.wallet_id, plan_price.original_price)
            if status:
                success_user.append(i.user_id)
                subscriptionSucess(i.user)
            else:
                subscriptionReject(i.user)
        current_date = datetime.now().date()
        all_users.filter(user_id__in=success_user).update(current_period_start=current_date, current_period_end=current_date+timedelta(days=30))
