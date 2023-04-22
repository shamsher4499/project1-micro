from django.urls import path
from . import views

urlpatterns = [
    #-------------------auth----------------------
    path('', views.home, name='home'),
    path('user-information/<str:slug>/', views.userInformation, name='user_information'),
    path('requestOTP-userProfile/<str:slug>/', views.userInformationRequestOTP, name='request_otp_profile'),
    path('verifyOTP-userProfile/<str:slug>/', views.userInformationVerifyOTP, name='verify_otp_profile'),
    path('privacyPolicy/', views.privacyPolicy, name='app_privacy_policy'),
    path('terms-conditions/', views.termConditions, name='app_term_conditions'),
    path('faq/', views.fAQ, name='app_faq'),
    path('blog/', views.blog, name='app_blog'),
    path('blog-detail/<str:blog_slug>/<str:slug>/', views.blogDetails, name='app_blog_detail'),
    path('about-us/', views.aboutUs, name='app_about_us'),
    path('contact-us/', views.contactUs, name='app_contact_us'),
    path('address/', views.useraddress, name='app_address'),
    path('profile/', views.userprofile, name='app_profile'),
    path('send-sms-to-verify-mob-num/', views.send_sms_to_verify_mob_num, name='app_send_sms_to_verify_mob_num'),
    path('verify-mobile-number/', views.verify_mobile_number, name='app_verify_mobile_number'),
    path('Edit-address/<str:slug>/', views.userEditaddress, name='app_edit_address'),
    path('delete-address/<str:slug>/', views.userDeleteAddress, name='app_delete_address'),
    path('notification-settings/', views.usernotificationSetting, name='app_notification_sittings'),
    path('subscriptionPlans', views.subscriptionListing, name='subscription_listing'),
    path('buy-subscription/<slug:slug>/', views.buySubscription, name='buy_subscription'),
]