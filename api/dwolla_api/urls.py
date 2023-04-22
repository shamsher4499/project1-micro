from django.urls import path
from .views import *

urlpatterns = [
    #-------------------auth----------------------
    path('dwollaCustomer/', CustomerAPI.as_view()),
    path('fundingSources/', FundingAPI.as_view()),
    path('transfer/', TransferAPI.as_view()),
    path('checkBalance/', CheckBalanceAPI.as_view()),
    path('transactionHistory/', TransactionsHistoryAPI.as_view()),
    path('verifyBank/', VerifyFundingSourceAPI.as_view()),
    path('verifyAmount/', VerifyAmountAPI.as_view()),

]