"""
Django settings for microApp project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import os
from django.contrib.messages import constants as messages
from decouple import config, Csv
from datetime import timedelta


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = config("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

AUTH_USER_MODEL='superadmin.User'
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'superadmin',
    # 'plaid_api',
    'rest_framework_simplejwt',
    "corsheaders",
    'django_celery_results',
    'django_celery_beat',
    'drf_yasg',

    #-------------------API-------------------
    'api.auth_api',
    'api.bid_api',
    'api.payment_api',
    'api.wallet_api',
    'api.store_api',
    'api.dwolla_api',
    'api.loan_api',
    'plaid_api',
    #---------------------------frontend--------------
    'app.home_app',
    'app.auth_app',
    'app.borrower_app',
    'app.lender_app',
    'app.loan_app',

    'django.contrib.sites', # must
    'allauth', # must
    'allauth.account', # must
    'allauth.socialaccount', # must
    'allauth.socialaccount.providers.google', # new

    # 'debug_toolbar',


]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_session_timeout.middleware.SessionTimeoutMiddleware',
    'api.csrf_token_middleware.CsrfExemptMiddleware'
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = 'microApp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [],
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'microApp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUEST': True,
    }
}

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': 'micro',
#        'USER': 'postgres',
#        'PASSWORD': 'postgres',
#        'HOST': 'localhost',
#        'PORT': '5432',
#        'ATOMIC_REQUEST': True,
#    }
# }

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_L10N = True

USE_TZ = False


REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
     'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.custom_error.CustomJWTAuthentication',
    ),
    # 'DEFAULT_PARSER_CLASSES': [
    #     'rest_framework.parsers.FileUploadParser',
    #     'rest_framework.parsers.JSONParser',
    # ],
    'EXCEPTION_HANDLER': 'api.custom_throttling.custom_exception_handler',
    # 'DEFAULT_THROTTLE_CLASSES': [
    #     'rest_framework.throttling.AnonRateThrottle',
    #     'rest_framework.throttling.UserRateThrottle'
    # ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/day',
        'user': '5/hour'
    }
}


JWT_SECRET_KEY = config('JWT_SECRET_KEY')


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),
    # 'ACCESS_TOKEN_LIFETIME': timedelta(minutes=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': JWT_SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]


#For SMTP configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

#Plaid configuration
CLIENT_ID = '630c675c80d8f00014d418b8'
PLAID_SECRET_KEY = '4e3db63a98a033e067fcaf291e8b37'
PLAID_PUBLIC_KEY = ''
SANDBOX_ONLY = 'sandbox.plaid.com'
PLAID_ENVIRONMENT = ''
WEBHOOK_URL = 'https://www.genericwebhookurl.com/webhook'

INTERNAL_IPS = [
    "127.0.0.1",
    "172.16.2.139",
    'localhost',
]

# LOGIN_URL = "/"

#----message broker-----------------
CELERY_BROKER_URL = "redis://redis:6379"
CELERY_RESULT_BACKEND = "redis://redis:6379"
CELERY_CACHE_BACKEND = 'django-cache'


#Stripe
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_ENDPOINT_SECRET = config('STRIPE_ENDPOINT_SECRET')

SUCCESS_URL = config('SUCCESS_URL')
CANCEL_URL = config('CANCEL_URL')

WEBSITE_URL = config('WEBSITE_URL')


#----session settings------------
SESSION_EXPIRE_SECONDS = 3600  # 1 hour
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_TIMEOUT_REDIRECT = '/auth/signIn/'


#-----DWOLLA settings-------------
DWOLLA_CLIENT_ID = config('DWOLLA_CLIENT_ID')
DWOLLA_CLIENT_SECRET = config('DWOLLA_CLIENT_SECRET')
DWOLLA_ENVIRONMENT = config('DWOLLA_ENVIRONMENT')


# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:8080",
# ]

CORS_ORIGIN_WHITELIST = (
  'http://127.0.0.1',
  'http://127.0.0.1:8000',
  'http://localhost',
  'http://localhost:8000',
  'http://172.16.11.95:8000',
)

CORS_ORIGIN_ALLOW_ALL = True


#Social auth configuration settings.....
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    # 'allauth.account.auth_backends.AuthenticationBackend',
]

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
SOCIALACCOUNT_AUTO_SIGNUP = True    

LOGIN_REDIRECT_URL = '/'

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
GOOGLE_SECRET_KEY = config('GOOGLE_SECRET_KEY')


#FCM token server key
FIREBASE_SERVER_KEY = config('FIREBASE_SERVER_KEY')


SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "METHOD": "oauth2",
        'SCOPE': [
            'profile',
            'email',
        ],
        "FIELDS": [
            "id",
            "first_name",
            "email",
            "last_name",
            "name",
        ],
        "APP": {
            "client_id": config('GOOGLE_CLIENT_ID'), 
            "secret": config('GOOGLE_SECRET_KEY'),
            "key": "",
        },
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#Swagger configuration
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'basic': {
            'type': 'basic',
        }
    },
}


DATA_UPLOAD_MAX_MEMORY_SIZE = 15728640