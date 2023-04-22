from allauth.account.signals import user_signed_up
from .models import User
from django.dispatch import Signal, receiver

@receiver(user_signed_up)
def saveUser(sender=User, **kwargs):
    pass




