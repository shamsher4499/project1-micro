from time import sleep
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from superadmin.models import *
from datetime import datetime
from .utils import checkout_subscriptions

# @shared_task
# def add(x, y):
#     return x + y

@shared_task
def user_subscription():
    checkout_subscriptions()
    return True

# @shared_task
def loginAlertByCelery(user_data, location):
    email = EmailTemplate.objects.get(name='Login Alert')
    user = User.objects.get(email=user_data)
    subject = email.name
    data = email.editor
    if location.get("city") != None:
        if user.name != None:
            message = data.format(name=user.name, last_login=user.last_login, ip_address=location.get("ip"), city=location.get("city"), region=location.get("region"), country=location.get("country"))
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
        else:
            message = data.format(name='User')
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
    else:
        if user.name != None:
            message = data.format(name=user.name, last_login=user.last_login, ip_address=location.get("ip"), city='Los Angeles', region='California', country='United States')
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
        else:
            message = data.format(name='User')
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])