from django.urls import path
from . import views

urlpatterns = [
    #-------------------auth----------------------
    path('dashboard/', views.borrowerDashboard, name='app_dashboard'),
    path('create-bid-request/', views.createBidRequest, name='app_create_bid_request'),
    path('reject-bid-request/<slug:slug>/', views.rejectBidRequest, name='app_reject_bid_request'),
    path('cashuu-score/', views.usercashuuScore, name='app_cashuu_score'),
    path('bid-request/', views.userbid, name='app_bid_request'),
    path('lending-box-detail/<slug:store_profile_slug>', views.lendingBoxDetail, name='app_lending_box_detail'),
    path('my-banks/', views.userAccounts, name='user_accounts'),
    path('create-dwolla-account/', views.createDwollaAccount, name='create_dwolla_account'),
    path('delete-plaid-account/<str:funding_source_id>', views.deletePlaidAccount, name='delete_plaid_account'),
    # path('loans-history/', views.userLoanHistory, name='app_loan_history'),
    # path('wallet/', views.userWallet, name='app_lender_wallet'),
    # path('address/', views.useraddress, name='app_address'),
    # path('Edit-address/<str:slug>/', views.userEditaddress, name='app_edit_address'),
    # path('delete-address/<str:slug>/', views.userDeleteAddress, name='app_delete_address'),
    # path('notification-settings/', views.usernotificationSetting, name='app_notification_sittings'),

]