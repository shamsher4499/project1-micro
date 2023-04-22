from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('active/', ActiveLoanAPI.as_view()),
    path('completed/', CompletedLoanAPI.as_view()),
    path('transferLoan-UserList/', TransferLoanUserAPI.as_view()),
    path('transferLoans/', TransferLoanAPI.as_view()),
    path('transferRequest-status/', TransferLoanRequestStatusAPI.as_view()),
    path('loanEMI/', EmiScheduleAPI.as_view()),
]