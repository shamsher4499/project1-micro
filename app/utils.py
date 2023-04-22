import re
import stripe
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY

docs_type = ['pdf', 'jpg', 'jpeg', 'png', 'docs', 'xls', 'csv']

def get_size(file):
    return file.size <= 2*1048576

def check_password(password):
    return bool(re.match('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).{8,16}$', password))==True