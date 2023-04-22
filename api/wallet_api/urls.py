from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('addLenderAmount/', LenderAddAmountAPI.as_view()),
    path('walletTransactions/', LenderWalletTransactionAPI.as_view()),
]