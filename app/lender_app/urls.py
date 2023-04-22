from django.urls import path
from . import views

urlpatterns = [
    # path('wallet/', views.userWallet, name='app_lender_wallet'),
    path('history/', views.userHistory, name='app_lender_history'),
    path('dashboard/', views.userDashboard, name='app_lender_dashboard'),
    path('bid/', views.lenderBid, name='app_lender_bid'),

]