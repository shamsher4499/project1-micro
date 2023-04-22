from django.urls import path
from . import views
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    #-------------------auth----------------------
    path('fileUpload/', FileUploadView.as_view()),
    
    path('register/', RegisterAPI.as_view()),
    path('otp-verify/', VerifyOTPAPI.as_view()),
    path('resend-otp/', ResendOTPAPI.as_view()),
    path('login/', LoginUser.as_view(), name='user_login_api'),
    path('changePassword/', PasswordResetAPI.as_view()),
    path('forgetPasswordStep1/', ChangePasswordSendMailAPI.as_view()),
    path('forgetPasswordStep2/', ChangePasswordVerifyOTPAPI.as_view()),
    path('forgetPasswordStep3/', ChangePasswordAPI.as_view()),
    path('mobile-login/', MobileLoginUserAPI.as_view()),
    path('mobile-otp-verify/', VerifyMobileOTPAPI.as_view()),
    path('mobile-forgetPassword1/', ChangePasswordSendMobileOTPAPI.as_view()),
    path('mobile-forgetPassword2/', ChangePasswordMobileOTPVerifyAPI.as_view()),
    path('mobile-forgetPassword3/', ChangePasswordMobileAPI.as_view()),
    path('mobileNumber-verify/', MobileNumberVerifyAPI.as_view()),
    path('mobileNumberOTP-verify/', MobileNumberOTPVerifyAPI.as_view()),
    path('address/', AddressAPI.as_view()),
    path('contactList/', ContactListAPI.as_view()),
    path('appIntro/', AppIntroAPI.as_view()),
    path('contact-us/', ContactUsAPI.as_view()),
    path('logout/', LogoutAPI.as_view()),
    path('profile/', ProfileAPI.as_view()),
    path('resend-mobile-otp/', ResendSendMobileOTPAPI.as_view()),
    path('notification-settings/', NotificationSettingsAPI.as_view()),
    path('sideMenu/', SideMenuListAPI.as_view()),
    path('user-information/', UserInfoAPI.as_view()),
    path('statesCodes/', StatesAPI.as_view()),

    #--------------------JWT-token---------------------
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('generateAccessToken/', TokenRefreshView.as_view(), name='token_refresh'),

]