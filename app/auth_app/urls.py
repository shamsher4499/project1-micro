from django.urls import path
from . import views

urlpatterns = [
    #-------------------auth----------------------
    path('SignUp/Borrower/', views.signUpUser, name='borrower_sign_up'),
    # path('SignUp/Lender/', views.signUpLender, name='lender_sign_up'),
    path('signIn/', views.signIn, name='user_sign_in'),
    path('forgetPassword-setp1/', views.forgetPasswordStep1, name='app_forget_password1'),
    path('forgetPassword-setp2/<str:slug>/', views.forgetPasswordStep2, name='app_forget_password2'),
    path('forgetPassword-setp3/<str:slug>/<str:user_slug>/', views.forgetPasswordStep3, name='app_forget_password3'),
    path('registration-successfully/', views.successRegistration, name='registration_successfully'),
    path('emailVerify/<str:slug>/', views.emailVerify, name='email_verify'),
    path('logout/', views.logoutUser, name='user_logout'),
    path('changePassword/', views.changePassword, name='user_change_password'),

]