from superadmin.models import *
from datetime import date


def change_status(user_loan):
    if user_loan > 20:
        return "PREMIUM"
    elif user_loan > 10:
        return "PRO"
    else:
        return "NEW"


def changeCategory():
    user_data = StoreProfile.objects.all()
    change_status = ['NEW', 'PRO', 'PREMIUM']
    pass