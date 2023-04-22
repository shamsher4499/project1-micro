from django.urls import path
from .views import *

urlpatterns = [
    path('generateToken/', PlaidItemTokenAPI.as_view()),
    path('addBankAccount/', FundingSourceAPI.as_view()),
    path('addBankAccountForWeb/', FundingSourceAPIForWeb.as_view(), name="add_plaid_bank_account_for_web")
]
