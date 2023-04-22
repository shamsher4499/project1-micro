from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('card-token/', CardTokenAPI.as_view()),
    path('user-SubscriptionPlans/', UserPlanAPI.as_view()),
    path('store-SubscriptionPlans/', StorePlanAPI.as_view()),
    path('set_default_card/', DefaultCardAPI.as_view()),
]