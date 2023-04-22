from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(
   openapi.Info(
      title="Cashuu Web API",
      default_version='v1',
      description="Cashuu api docs",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

   #  path('admin/', admin.site.urls),
    # path('plaid/', include('plaid_api.urls')),
    path('adminpanel/', include('superadmin.urls')),
    
    path('accounts/', include('allauth.urls')),
    #-----------------api urls------------------------
    path('api/v1/auth/', include('api.auth_api.urls')), 
    path('api/v1/bid/', include('api.bid_api.urls')),
    path('api/v1/payment/', include('api.payment_api.urls')),
    path('api/v1/wallet/', include('api.wallet_api.urls')),
    path('api/v1/store/', include('api.store_api.urls')),
    path('api/v1/dwolla/', include('api.dwolla_api.urls')),
    path('api/v1/loan/', include('api.loan_api.urls')),
    path('api/v1/plaid/', include('plaid_api.urls')),
    #-----------------end--api urls--------------------

    #-----------------app urls------------------------
    path('', include('app.home_app.urls')),
    path('auth/', include('app.auth_app.urls')),
    path('user/', include('app.borrower_app.urls')),
    path('lender/', include('app.lender_app.urls')),
    path('loan/', include('app.loan_app.urls')),
    #-----------------end--app urls---------------------
    # path('__debug__/', include('debug_toolbar.urls')),

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "microApp.views.page_not_found_view"