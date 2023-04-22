from django.urls import path
from . import views

urlpatterns = [
    path('wallet/', views.userWallet, name='app_lender_wallet'),
    path('check-wallet-amount-max-limit/', views.check_wallet_amount_max_limit, name='app_check_wallet_amount_max_limit'),
    path('transfer-to-wallet/', views.transfer_to_wallet, name='app_transfer_to_wallet'),
    # path('history/', views.userHistory, name='app_lender_history'),
    # path('dashboard/', views.userDashboard, name='app_lender_dashboard'),
    # path('bid/', views.userBid, name='app_lender_bid'),
    path('borrowerLoan-history', views.borrowerLoanHistory, name='user_loan_history'),
    path('lenderLoan-history', views.lenderLoanHistory, name='lender_loan_history'),
    path('lendingBox-Loan-history', views.lendingBoxLoanHistory, name='lending_box_loan_history'),
    
]