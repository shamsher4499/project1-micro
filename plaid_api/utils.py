from plaid import Client
import plaid
import requests
from django.conf import settings
import json
from dataclasses import dataclass

plaid_client = Client(client_id=settings.CLIENT_ID, secret=settings.PLAID_SECRET_KEY, environment=settings.PLAID_ENVIRONMENT)

@dataclass
class ItemToken:
    def create_link_token():
        url = 'https://sandbox.plaid.com/link/token/create'
        config = {
            "client_id": settings.CLIENT_ID,
            "secret": settings.PLAID_SECRET_KEY,
            'user': {
                'client_user_id': '8be89412-27ea-41b0-b549-4e687bb7971c'
            },
            'products': ['auth', 'transactions'],
            'client_name': 'Cashuu app',
            'country_codes': ['US'],
            'language': 'en',
            'webhook': 'http://cashuu.devtechnosys.tech/',
            'link_customization_name': 'default',
            'redirect_uri': 'https://cashuu.devtechnosys.tech/',   
            'account_filters': {
                'depository': {
                    'account_subtypes': ['checking', 'savings'],
                },
            },
        }
        headersList = {
            "Accept": "*/*",
            "Content-Type": "application/json" 
            }
        
        try:
            plaid_data = requests.post(url, data=json.dumps(config), headers=headersList)
            return plaid_data.text
        except:
            return plaid_data.status_code
        

    def get_link_token(item_token):
        url = 'https://sandbox.plaid.com/link/token/get'
        config = {
            "client_id": settings.CLIENT_ID,
            "secret": settings.PLAID_SECRET_KEY,
            'link_token': item_token,
        }
        headersList = {
            "Accept": "*/*",
            "Content-Type": "application/json" 
            }
        try:
            plaid_data = requests.post(url, data=json.dumps(config), headers=headersList)
            return plaid_data.text
        except:
            return plaid_data.status_code
        
@dataclass
class Institutions:
    def get_institutions():
        url = 'https://sandbox.plaid.com/institutions/get'
        config = {
            "client_id": settings.CLIENT_ID,
            "secret": settings.PLAID_SECRET_KEY,
            "country_codes": ['US'],
            'count': 10,
            "offset":10
        }
        headersList = {
            "Accept": "*/*",
            "Content-Type": "application/json" 
            }
        try:
            plaid_data = requests.post(url, data=json.dumps(config), headers=headersList)
            return plaid_data.json()
        except:
            return plaid_data.status_code
        
@dataclass
class ExchangeToken:
    def exchange_token(public_token):
        url = 'https://sandbox.plaid.com/item/public_token/exchange'
        config = {
            "client_id": settings.CLIENT_ID,
            "secret": settings.PLAID_SECRET_KEY,
            "public_token":public_token
        }
        headersList = {
            "Accept": "*/*",
            "Content-Type": "application/json" 
            }
        try:
            plaid_data = requests.post(url, data=json.dumps(config), headers=headersList)
            return plaid_data.json() if plaid_data.status_code == 200 else 400
        except:
            return plaid_data.status_code
        
@dataclass
class ProcessorToken:
    def processor_token(access_token, account_id):
        url = 'https://sandbox.plaid.com/processor/token/create'
        config = {
            "client_id": settings.CLIENT_ID,
            "secret": settings.PLAID_SECRET_KEY,
            "access_token":access_token,
            "account_id":f'{account_id}',
            "processor":'dwolla'
        }
        headersList = {
            "Accept": "*/*",
            "Content-Type": "application/json" 
            }
        try:
            plaid_data = requests.post(url, data=json.dumps(config), headers=headersList)
            return plaid_data.json() if plaid_data.status_code == 200 else 400
        except:
            return plaid_data.status_code