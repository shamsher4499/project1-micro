from django.http import JsonResponse
from django.conf import settings
from dataclasses import dataclass
from .utils import get_ip
from .dwolla_token import dwollo_client, generate_access_token

DWOLLA_CLIENT_ID =  settings.DWOLLA_CLIENT_ID
DWOLLA_CLIENT_SECRET =  settings.DWOLLA_CLIENT_SECRET
DWOLLA_ENVIRONMENT =  settings.DWOLLA_ENVIRONMENT


@dataclass
class DwollaCustomerAPI:
    def create_customer(customer):
        url = 'https://api.dwolla.com/customers'
        ip_address = get_ip()
        request_body = {
            'firstName': customer.get('firstName', None),
            'lastName': customer.get('lastName', None),
            'email': customer.get('email', None),
            'type': customer.get('type', 'personal'),
            "address1": customer.get('address1', ''),
            "city": customer.get('city', ''),
            "state": customer.get('state', ''),
            "postalCode": customer.get('postalCode', ''),
            "dateOfBirth": customer.get('dateOfBirth', ''),
            "ssn": customer.get('ssn', ''),
            'ipAddress': ip_address if ip_address else '99.99.99.99',
            }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_data = access_token.post(url, request_body)
        return customer_data.headers['Location'].split('/')[-1]

    def get_customer(customer_id):
        url = f'https://api.dwolla.com/customers/{customer_id}'
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_data = access_token.get(url)
        return customer_data.body

    def get_all_customers(self, customer):
        pass

    def update_customer(customer):
        customer_id = customer.get('customer_id', None)
        url = f'https://api-sandbox.dwolla.com/customers/{customer_id}'
        ip_address = get_ip()
        request_body = {
            'firstName': customer.get('firstName', None),
            'lastName': customer.get('lastName', None),
            'email': customer.get('email', None),
            'type': customer.get('type', None),
            'businessName': customer.get('businessName', None),
            "address1": customer.get('address1', None),
            "address2": customer.get('address2', None),
            "city": customer.get('city', None),
            "state": customer.get('state', None),
            "postalCode": customer.get('postalCode', None),
            "dateOfBirth": customer.get('dateOfBirth', None),
            "ssn": customer.get('ssn', None),
            'ipAddress': ip_address if ip_address else '99.99.99.99',
        }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_data = access_token.post(url, request_body)
        return customer_data.body

    def delete_customer(self, customer):
        pass

    def verify_customer(self, customer):
        pass

@dataclass
class BeneficialAPI:
    def create_beneficial(customer):
        customer_id = customer.get('id')
        # try:
        url = f'https://api.dwolla.com/customers/{customer_id}/beneficial-owners'
        # ip_address = get_ip()
        # request_body = {
        #     'firstName': customer.get('firstName', 'dishank'),
        #     'lastName': customer.get('lastName', 'biyani'),
        #     'dateOfBirth': customer.get('dateOfBirth', '1970-01-01'),
        #     'ssn': customer.get('ssn', '123-46-7890'),
        #     'address': {
        #         'address1': customer.get('address1', '99-99 33rd St'),
        #         'city': customer.get('city', 'Jaipur'),
        #         'stateProvinceRegion': customer.get('stateProvinceRegion', 'NY'),
        #         'country': customer.get('country', 'US'),
        #         'postalCode': customer.get('postalCode', '11101')
        #     }
        #     }
        request_body = {
            'firstName': 'John',
            'lastName': 'Doe',
            'dateOfBirth': '1970-01-01',
            'ssn': '123-46-7890',
            'address': {
                'address1': '99-99 33rd St',
                'city': 'Some City',
                'stateProvinceRegion': 'NY',
                'country': 'US',
                'postalCode': '11101'
            }
            }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_data = access_token.post(url, request_body)
        return customer_data.headers['Location'].split('/')[-1]
        # except:
        #     return None

@dataclass
class DwollaFundingSourceAPI:
    def create_funding(customer):
        customer_url = f'https://api-sandbox.dwolla.com/customers/{customer.get("dwolla_id")}'
        request_body = {
            'routingNumber': customer.get('routingNumber', None),
            'accountNumber': customer.get('accountNumber', None),
            'bankAccountType': customer.get('bankAccountType', None),
            'name': customer.get('name', None)
            }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_bank = access_token.post(f'{customer_url}/funding-sources', request_body)
        return customer_bank.headers['Location'].split('/')[-1]

    def get_wallet(customer):
        url = f'https://api.dwolla.com/customers/{customer}/funding-sources'
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_data = access_token.get(url)
        return customer_data.body['_embedded']['funding-sources'][0]['id']

    def get_all_funding(customer):
        url = f'https://api.dwolla.com/customers/{customer}/funding-sources'
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_data = access_token.get(url)
        return customer_data.body['_embedded']['funding-sources']

    def remove_funding(function_id):
        url = f'https://api.dwolla.com/funding-sources/{function_id}'
        request_body = {
            'removed': True
            }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        function_status = access_token.post(url, request_body)
        return function_status.body

@dataclass
class DwollaTransferAPI:
    def create_transfer(transfer_data):
        url = f'https://api.dwolla.com/transfers'
        funding_source = f'https://api-sandbox.dwolla.com/funding-sources/{transfer_data.get("funding_source")}'
        destination_source = f'https://api-sandbox.dwolla.com/funding-sources/{transfer_data.get("destination_source")}'
        request_body = {
            '_links': {
                'source': {
                'href': funding_source,
                },
                'destination': {
                'href': destination_source,
                }
            },
            'amount': {
                'currency': 'USD',
                'value': f"{float(transfer_data.get('amount'))}"
            },
            "clearing": {
                "destination": "next-available"
            },
        }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        transfer = access_token.post(url, request_body)
        return transfer.headers['Location']

@dataclass
class DwollaCheckBalanceAPI:
    def get_balance(source_id):
        url = f'https://api.dwolla.com/funding-sources/{source_id}/balance'
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_balance = access_token.get(url)
        return customer_balance.body['total']
    
@dataclass
class DwollaVerifyAPI:
    def verify_status(source_id):
        url = f'https://api.dwolla.com/funding-sources/{source_id}/micro-deposits'
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_bank = access_token.post(url)
        return customer_bank.body
    
    def verify_amount(source_id):
        url = f'https://api.dwolla.com/funding-sources/{source_id["funding_id"]}/micro-deposits'
        request_body = {
            'amount1': {
                'value': f'{source_id["amount_1"]}',
                'currency': 'USD'
            },
            'amount2': {
                'value': f'{source_id["amount_2"]}',
                'currency': 'USD'
            }
        }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_balance = access_token.post(url, request_body)
        return customer_balance.body

@dataclass
class DwollaTransactionHistoryAPI:
    def all_transactions(customer_id):
        url = f'https://api.dwolla.com/customers/{customer_id}/transfers'
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_history = access_token.get(url)
        return customer_history.body['_embedded']['transfers']

@dataclass
class DwollaTransactionStatusAPI:
    def transaction_status(transaction_id):
        url = f'https://api.dwolla.com/transfers/{transaction_id}'
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        customer_history = access_token.get(url)
        return customer_history.body['status']

def check_wallet_amount(**kwargs) -> bool:
    user_wallet = DwollaCheckBalanceAPI.get_balance(kwargs['wallet_id'])
    if float(user_wallet['value']) >= float(kwargs['amount']):
        return True
    else:
        return False
    
@dataclass
class DwollaSubscriptionAPI:
    def create_subscription(wallet_id, price):
        url = f'https://api.dwolla.com/transfers'
        funding_source = f'https://api-sandbox.dwolla.com/funding-sources/{wallet_id}'
        destination_source = f'https://api-sandbox.dwolla.com/funding-sources/35df25ba-486d-48ba-a6b2-2d6de65950a0'
        request_body = {
            '_links': {
                'source': {
                'href': funding_source,
                },
                'destination': {
                'href': destination_source,
                }
            },
            'amount': {
                'currency': 'USD',
                'value': f"{price}"
            },
            "clearing": {
                "source": "next-available"
            },
        }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        transfer = access_token.post(url, request_body)
        return transfer.status == 201
    
@dataclass
class DwollaPlaidAPI:
    def create_plaid_token(customer_data, processor_token):
        url = f'https://api.dwolla.com/customers/{customer_data["customer_id"]}/funding-sources'
        request_body = {
            'plaidToken': processor_token,
            'name': f'{customer_data["name"]}'
            }
        client = dwollo_client()
        access_token = client.Token(access_token = generate_access_token(), expires_in = 123)
        account_info = access_token.post(url, request_body)
        return account_info.headers['Location'].split('/')[-1]