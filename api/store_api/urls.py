from django.urls import path
from . import views
from .views import *

urlpatterns = [
    #-------------------auth----------------------
    path('register/', StoreRegisterAPI.as_view()),
    path('profile/', StoreProfileAPI.as_view()),
    path('storeRating/', StoreRatingAPI.as_view()),
    path('avgTicket/', StoreAvgTicketAPI.as_view()),
    path('storeBusinessType/', StoreBusinessAPI.as_view()),
    path('storeLoan/', StoreLoanAPI.as_view()),
    path('storeLoanRequest/', StoreLoanRequestAPI.as_view()),

]