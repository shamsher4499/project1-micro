from django.conf import settings
import dwollav2

app_key = settings.DWOLLA_CLIENT_ID
app_secret = settings.DWOLLA_CLIENT_SECRET

def generate_access_token():
    client = dwollav2.Client(
                key = app_key,
                secret = app_secret,
                environment = 'sandbox') # optional - defaults to production
    application_token = client.Auth.client()
    return application_token.access_token

def dwollo_client():
    client = dwollav2.Client(
                key = app_key,
                secret = app_secret,
                environment = 'sandbox')
    return client