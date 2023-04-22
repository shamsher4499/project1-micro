from django.contrib.auth.models import auth
from django.conf import settings
from superadmin.models import *
from .serializers import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction, IntegrityError
import re
from api.fake_email import *
from .email import *
from api.utils import *
from rest_framework import status
from api.jwt import *
import jwt
import json
import time
from datetime import datetime, timedelta
from drf_yasg.utils import swagger_auto_schema
from api.push_notifications import push_notification
import threading
from api.custom_threading import threaded_function

def check_password(password):
    return bool(re.match('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).{8,16}$', password))==True


class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)
    def post(self, request):
        data = request.data
        file_data = data['file']
        name = data['name']
        if check_similar_image(f'sample/{file_data.name}', 'sample/valid_id.jpg'):
        # if check_valid_pdf(f'sample/{file_data.name}'):
            start_time = time.time()
            destination = open('sample/' + file_data.name, 'wb+')
            for chunk in file_data.chunks():
                destination.write(chunk)
            destination.close()
            return Response(
                {
                    'name':name,
                    'total_uploading_time':time.time() - start_time
                },
                status.HTTP_202_ACCEPTED
                )
        else:
            return Response(
            {
                'status':False,
                'message':'File must have valid Tax ID.'
            },
            status.HTTP_406_NOT_ACCEPTABLE
            )

class RegisterAPI(APIView):
    parser_classes = [MultiPartParser]
    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        try:
            check = request.META['CONTENT_TYPE'].split(';')[1].split('=')
            if request.META['CONTENT_TYPE'].split(';')[0] == 'multipart/form-data' and check[0].strip() == 'boundary':
                data = request.data
                if not data:
                    return Response({
                        'status': False,
                        'message': 'Please input valid data.'
                    })
                serializer = RegisterSerializer(data=data)
                if not serializer.is_valid(raise_exception=False):
                    return Response({
                        'status': False,
                        'message': 'Please input valid data.'
                    })
                if not (BlockEmailDomain.objects.filter(domain__contains=data['email'].split('@')[1], is_active=True) or data['email'].split('@')[1] in fake_email_list):
                    if User.objects.filter(email=data['email'].lower()).exists():
                        return Response({
                            'status': False,
                            'message': 'This Email address already registered.',
                        })
                    if User.objects.filter(mobile=data['mobile']).exists():
                        return Response({
                            'status': False,
                            'message': 'Mobile Number must be uniuqe.',
                        })
                    if len(data['mobile']) != 10 or not data['mobile'].isnumeric():
                        return Response({
                            'status': False,
                            'message': 'Mobile number must be numeric and 10 digit',
                        })
                    if not (data['document'].name.split('.')[-1]).lower() in docs_type:
                        return Response({
                            'status': False,
                            'message': 'Document type must be pdf,png,jpeg,xls only.',
                        })
                    if not get_size(data['document']):
                        return Response({
                            'status': False,
                            'message': 'File size must be less than 5 MB.',
                        })
                    if not check_ssn(data['social_security_number']):
                        return Response({
                            'status': False,
                            'message': 'SSN must be valid or 9 digit only.',
                        })
                    try:
                        customer_data = {
                            'firstName': data.get('firstName', None),
                            'lastName': data.get('lastName', None),
                            'email': data.get('email', None),
                            'type': data.get('type', 'personal'),
                            "address1": data.get('address', ''),
                            "city": data.get('city', ''),
                            "state": data.get('state', ''),
                            "postalCode": data.get('postalCode', ''),
                            "dateOfBirth": data.get('dateOfBirth', ''),
                            "ssn": data.get('social_security_number', ''),
                            }
                        user = User(email=data['email'].lower(), name=data['firstName']+' '+data['lastName'], mobile=data['mobile'],
                        document=data['document'], country_code=data['country_code'], calling_code=data['calling_code'], 
                        social_security_number=data['social_security_number']) 
                        user.set_password(data['password'])
                        user.save_with_slug()
                        user.save()
                        sendOTP(user)
                        # multiprocessing_wrapper(customer_data, user.id)
                        t = threading.Thread(target=threaded_function, args=(customer_data,user.id))
                        t.start()
                        return Response({
                            'status': True,
                            'message': 'Verification code sent on the mail address. Please check',
                        })
                    # except DwollaError as e:
                    #     return Response(
                    #         {
                    #             'status':False,
                    #             'message': e.body['_embedded']['errors'][0]['message']
                    #         },
                    #         e.status
                    #         )   
                    except:
                        return Response({
                            'status': False,
                            'message': 'Dwolla facing huge traffic now. Please try again.',
                        })
                else:
                    return Response({
                        'status': False,
                        'message': 'Email address not acceptable. Please use valid domain.',
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Content type must be in multipart/form-data'
                })
        except:
            return Response({
                'status': False,
                'message': 'Something went wrong!'
            })

class VerifyOTPAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=VerifyOTPSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if not data:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!",
                    })
                serializer = VerifyOTPSerializer(data=data)
                if not serializer.is_valid():
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!",
                    })
                if not User.objects.filter(email=data["email"].lower()).exists():
                    return Response({
                        "status": False,
                        "message": "Email not found."
                    })
                user = User.objects.get(email=data["email"].lower())
                if len(data['otp']) != 4 and not data['otp'].isnumeric():
                    return Response({
                        "status": False,
                        "message": "OTP must be 4 digit and numeric only.",
                    })
                if user.is_verified == True:
                    return Response({
                        "status": False,
                        "message": "You have already verified.",
                    })
                if user.otp != data["otp"]:
                    return Response({
                        "status": False,
                        "message": "OTP not match. Please try again.",
                    })
                user.is_verified = True
                user.is_active = True
                user.otp = ""
                user.save()
                refresh = RefreshToken.for_user(user)
                user_data = UserSerializer(user)
                return Response({
                    "status": True,
                    "token": str(refresh.access_token),
                    "refreshToken": str(refresh),
                    "payload": user_data.data,
                    "message": "Email Verification is successfully completed.",
                })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something went wrong!",
            })

class ResendOTPAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=ResendOTPSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if not data:
                    return Response( {
                        "status": False,
                        "message": "Please input valid data.",
                    })
                serializer = ResendOTPSerializer(data=data)
                if not serializer.is_valid():
                    return Response({
                        "status": False,
                        "message": 'Please input valid data.'
                    })
                if data['email'] != 'None':
                    if not User.objects.filter(email=data["email"].lower()).exists():
                        return Response({
                                "status": False,
                                "message": "Email not found!",
                            })
                    user = User.objects.get(email=data["email"].lower())
                    if user.otp_sent_time != None:
                        filter_date = str(user.otp_sent_time)[:19]
                        now_plus_5 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
                        if datetime.now() >= now_plus_5:
                            sendOTP(user)
                            user.otp_sent_time = datetime.now()
                            user.save()
                            return Response({
                                "status": True,
                                "message": "Verification code sent on the mail address. Please check",
                            })
                        else:
                            return Response({
                                "status": False,
                                "message": f"You can send next otp after 1 minutes. Please try after {str(now_plus_5)[11:]}.",
                            })
                    else:
                        sendOTP(user)
                        user.otp_sent_time = datetime.now()
                        user.save()
                        return Response({
                            "status": True,
                            "message": "Verification code sent on the mail address. Please check",
                        })
                if data['mobile'] == 'None':
                    return Response({
                        "status": False,
                        "message": "Please select email or mobile.",
                    })
                if (len(data["mobile"]) != 10 and not data["mobile"].isnumeric()):
                    return Response({
                        "status": False,
                        "message": "Mobile Number must be 10 digit or must be numeric only.",
                    }) 
                if not User.objects.filter(mobile=data["mobile"]).exists():
                    return Response({
                        "status": False,
                        "message": "Mobile Number not found.",
                    })
                user = User.objects.get(mobile=data["mobile"])
                mobile_data = user.mobile[6:10]
                if user.otp_sent_time == None:
                    if user.otp_count == str(0):
                        user.otp_count = int(user.otp_count) + 1
                        user.save()
                        return Response({
                            "status": True,
                            "message": f"OTP send successfully on ***{mobile_data}",
                        })
                    elif user.otp_count < str(3):
                        user.otp_count = int(user.otp_count) + 1
                        if user.otp_count == 3:
                            user.otp_sent_time = datetime.now()
                        user.save()
                        return Response({
                            "status": True,
                            "message": f"OTP send successfully on ***{mobile_data}",
                        })
                    else:
                        return Response({
                            "status": False,
                            "message": "Your otp send request limit is over for 1 Minute. Please try again after 1 Minute.",
                        })
                else:
                    filter_date = str(user.otp_sent_time)[:19]
                    now_plus_5 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
                    if datetime.now() >= now_plus_5:
                        user.otp_count = 1
                        user.otp_sent_time = None
                        user.save()
                        return Response({
                            "status": True,
                            "message": f"OTP send successfully on ***{mobile_data}",
                        })
                    else:
                        return Response({
                            "status": False,
                            "message": "Your otp send request limit is over for 1 Minute. Please try again after 1 Minute.",
                        })  
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something went wrong!",
            })

class LoginUser(APIView):
    # parser_classes = [JSONParser]
    permission_classes=[AllowAny]
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = LoginSerializer(data=data)
                    if serializer.is_valid():
                        if data['email'] != 'None':
                            if User.objects.filter(email=data["email"].lower(), is_superuser=False).exists():
                                user = User.objects.get(email=data["email"].lower())
                                if user.login_count == 3:
                                    filter_date = str(user.login_attempt_time)[:19]
                                    now_plus_5 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=5)
                                    if datetime.now() >= now_plus_5:
                                        if user.is_verified == False:
                                            sendOTP(user)
                                            userStatus = {
                                                'mobile_verified':user.mobile_verified,
                                                'is_verified':user.is_verified,
                                                'email':user.email,
                                            }
                                            return Response({
                                                "status": True,
                                                'payload':userStatus,
                                                "message": "Please check email, your email address is not verified yet.",
                                            })
                                        if not user.is_active == True:
                                            return Response({
                                                "status": False,
                                                "message": "Your Account is Inactive. Please contact the Admin.",
                                            })
                                        if not user.check_password(data["password"]):
                                            if user.login_count != 3:
                                                user.login_count += 1
                                                user.save()
                                                if user.login_count == 3:
                                                    user.login_attempt_time = datetime.now()
                                                    user.save()
                                                return Response({
                                                    "status": False,
                                                    "message": f"Incorrect Password. you have only {3-user.login_count} attempts left",
                                                })
                                            else:
                                                user.login_count = 0
                                                user.login_attempt_time = None
                                                user.save()
                                                if user.is_verified == False:
                                                    sendOTP(user)
                                                    userStatus = {
                                                        'mobile_verified':user.mobile_verified,
                                                        'is_verified':user.is_verified,
                                                        'email': user.email
                                                    }
                                                    return Response({
                                                        "status": True,
                                                        'payload':userStatus,
                                                        "message": "Please check mail, your email address is not verified yet.",
                                                    })
                                                if not user.is_active == True:
                                                    return Response({
                                                        "status": False,
                                                        "message": "Your Account is Inactive. Please contact the Admin.",
                                                    })
                                                if not user.check_password(data["password"]):
                                                    user.login_count += 1
                                                    user.save()
                                                    if user.login_count == 3:
                                                        user.login_attempt_time = datetime.now()
                                                        user.save()
                                                    return Response({
                                                        "status": False,
                                                        "message": f"Incorrect Password. you have only {3-user.login_count} attempts left",
                                                    })
                                                else:
                                                    user.login_count = 0
                                                    user.login_attempt_time = None
                                                    user.fcm_token = data['fcm_token']
                                                    user.save()
                                                    user_view = UserSerializer(user, context={'user_id':user.id})
                                                    refresh = RefreshToken.for_user(user)
                                                    auth.authenticate(email=data["email"].lower(), password=data["password"])
                                                    auth.login(request, user)
                                                    return Response({
                                                        "status": True,
                                                        "token": str(refresh.access_token),
                                                        "refreshToken": str(refresh),
                                                        "payload": user_view.data,
                                                        "message": "Login Success."
                                                    })
                                        else:
                                            user.login_count = 0
                                            user.login_attempt_time = None
                                            user.email_sent = True
                                            user.fcm_token = data['fcm_token']
                                            user.save()
                                            user_view = UserSerializer(user, context={'user_id':user.id})
                                            refresh = RefreshToken.for_user(user)
                                            auth.authenticate(email=data["email"].lower(), password=data["password"])
                                            auth.login(request, user)
                                            return Response({
                                                "status": True,
                                                "token": str(refresh.access_token),
                                                "refreshToken": str(refresh),
                                                "payload": user_view.data,
                                                "message": "Login Success."
                                            },
                                            status.HTTP_200_OK
                                            )     
                                    else:
                                        login_time = str(now_plus_5)[11:]
                                        if user.email_sent == False:
                                            sendAccountBlocked(user, login_time)
                                            user.email_sent = True
                                            user.save()
                                        return Response( {
                                            "status": False,
                                            "message": f"Your Account has been blocked for 5 minutes. Please try after {str(now_plus_5)[11:]}",
                                        })
                                else:
                                    if user.is_verified == False:
                                        sendOTP(user)
                                        userStatus = {
                                            'mobile_verified':user.mobile_verified,
                                            'is_verified':user.is_verified,
                                            'email': user.email
                                        }
                                        return Response({
                                            "status": True,
                                            'payload':userStatus,
                                            "message": "Please check email, your email address is not verified yet.",
                                        })
                                    if not user.is_active == True:
                                        return Response({
                                            "status": False,
                                            "message": "Your Account is Inactive. Please contact the Admin.",
                                        })
                                    if not user.check_password(data["password"]):
                                        user.login_count += 1
                                        user.save()
                                        if user.login_count == 3:
                                            user.login_attempt_time = datetime.now()
                                            user.save()
                                        return Response({
                                            "status": False,
                                            "message": f"Incorrect Password. you have only {3-user.login_count} attempts left",
                                        })
                                    else:
                                        user.login_count = 0
                                        user.login_attempt_time = None
                                        user.email_sent = True
                                        user.fcm_token = data['fcm_token']
                                        user.save()
                                        user_view = UserSerializer(user, context={'user_id':user.id})
                                        refresh = RefreshToken.for_user(user)
                                        auth.authenticate(email=data["email"].lower(), password=data["password"])
                                        auth.login(request, user)
                                        return Response({
                                            "status": True,
                                            "token": str(refresh.access_token),
                                            "refreshToken": str(refresh),
                                            "payload": user_view.data,
                                            "message": "Login Success."
                                        })  
                            else:
                                return Response( {
                                    "status": False,
                                    "message": "Email not found.",
                                })
                        if data['mobile'] != 'None':
                            if User.objects.filter(mobile=data["mobile"]).exists():
                                user = User.objects.get(mobile=data["mobile"])
                                if user.login_count == 3:
                                    filter_date = str(user.login_attempt_time)[:19]
                                    now_plus_5 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=5)
                                    if datetime.now() >= now_plus_5:
                                        if user.mobile_verified == False:
                                            if user.is_verified == False:
                                                userStatus = {
                                                    'mobile_verified':user.mobile_verified,
                                                    'is_verified':user.is_verified,
                                                    'email': user.email
                                                }
                                                return Response({
                                                    "status": True,
                                                    'payload':userStatus,
                                                    "message": "Please check email, your email is not verified yet.",
                                                })
                                            else:
                                                userStatus = {
                                                    'mobile_verified':user.mobile_verified,
                                                    'is_verified':user.is_verified
                                                }
                                                return Response({
                                                    "status": True,
                                                    'payload':userStatus,
                                                    "message": "Your Mobile number is not verified yet.",
                                                })
                                        if user.is_verified == False:
                                            userStatus = {
                                                'mobile_verified':user.mobile_verified,
                                                'is_verified':user.is_verified,
                                                'email':user.email
                                            }
                                            sendOTP(user)
                                            return Response({
                                                "status": True,
                                                'payload':userStatus,
                                                "message": "Please check email, your email is not verified yet.",
                                            })
                                        if not user.is_active == True:
                                            return Response({
                                                "status": False,
                                                "message": "Your Account is Inactive. Please contact the Admin.",
                                            })
                                        if not user.check_password(data["password"]):
                                            if user.login_count != 3:
                                                user.login_count += 1
                                                user.save()
                                                if user.login_count == 3:
                                                    user.login_attempt_time = datetime.now()
                                                    user.save()
                                                return Response({
                                                    "status": False,
                                                    "message": f"Incorrect Password. you have only {3-user.login_count} attempts left",
                                                })
                                            else:
                                                user.login_count = 0
                                                user.login_attempt_time = None
                                                user.save()
                                                userStatus = {
                                                    'mobile_verified':user.mobile_verified,
                                                    'is_verified':user.is_verified
                                                }
                                                if user.mobile_verified == False:
                                                    return Response({
                                                        "status": True,
                                                        'payload':userStatus,
                                                        "message": "Your Mobile number is not verified yet.",
                                                    })
                                                if user.is_verified == False:
                                                    sendOTP(user)
                                                    userStatus = {
                                                        'mobile_verified':user.mobile_verified,
                                                        'is_verified':user.is_verified,
                                                        'email':user.email
                                                    }
                                                    return Response({
                                                        "status": True,
                                                        'payload':userStatus,
                                                        "message": "Please check mail, your email is not verified yet.",
                                                    })
                                                if not user.is_active == True:
                                                    return Response({
                                                        "status": False,
                                                        "message": "Your Account is Inactive. Please contact the Admin.",
                                                    })
                                                if not user.check_password(data["password"]):
                                                    user.login_count += 1
                                                    user.save()
                                                    if user.login_count == 3:
                                                        user.login_attempt_time = datetime.now()
                                                        user.save()
                                                    return Response({
                                                        "status": False,
                                                        "message": f"Incorrect Password. you have only {3-user.login_count} attempts left",
                                                    })
                                                else:
                                                    user.login_count = 0
                                                    user.login_attempt_time = None
                                                    user.fcm_token = data['fcm_token']
                                                    user.save()
                                                    user_view = UserSerializer(user, context={'user_id':user.id})
                                                    refresh = RefreshToken.for_user(user)
                                                    auth.authenticate(mobile=data["mobile"], password=data["password"])
                                                    auth.login(request, user)
                                                    return Response({
                                                        "status": True,
                                                        "token": str(refresh.access_token),
                                                        "refreshToken": str(refresh),
                                                        "payload": user_view.data,
                                                        "message": "Login Success."
                                                    })
                                        else:
                                            user.login_count = 0
                                            user.login_attempt_time = None
                                            user.email_sent = True
                                            user.fcm_token = data['fcm_token']
                                            user.save()
                                            user_view = UserSerializer(user, context={'user_id':user.id})
                                            refresh = RefreshToken.for_user(user)
                                            auth.authenticate(mobile=data["mobile"], password=data["password"])
                                            auth.login(request, user)
                                            return Response({
                                                "status": True,
                                                "token": str(refresh.access_token),
                                                "refreshToken": str(refresh),
                                                "payload": user_view.data,
                                                "message": "Login Success."
                                            })     
                                    else:
                                        login_time = str(now_plus_5)[11:]
                                        if user.email_sent == False:
                                            sendAccountBlocked(user, login_time)
                                            user.email_sent = True
                                            user.save()
                                        return Response( {
                                            "status": False,
                                            "message": f"Your Account has been blocked for 5 minutes. Please try after {str(now_plus_5)[11:]}",
                                        })
                                else:
                                    if user.mobile_verified == False:
                                        if user.is_verified == False:
                                            userStatus = {
                                                'mobile_verified':user.mobile_verified,
                                                'is_verified':user.is_verified,
                                                'email': user.email
                                            }
                                            return Response({
                                                "status": True,
                                                'payload':userStatus,
                                                "message": "Please check email, your email is not verified yet.",
                                            })
                                        else:
                                            userStatus = {
                                                'mobile_verified':user.mobile_verified,
                                                'is_verified':user.is_verified
                                            }
                                            return Response({
                                                "status": True,
                                                'payload':userStatus,
                                                "message": "Your Mobile number is not verified yet.",
                                            })
                                    if user.is_verified == False:
                                        sendOTP(user)
                                        userStatus = {
                                            'mobile_verified':user.mobile_verified,
                                            'is_verified':user.is_verified,
                                            'email':user.email
                                        }
                                        return Response({
                                            "status": True,
                                            'payload':userStatus,
                                            "message": "Please check email, your email is not verified yet.",
                                        })
                                    if not user.is_active == True:
                                        return Response({
                                            "status": False,
                                            "message": "Your Account is Inactive. Please contact the Admin.",
                                        })
                                    if not user.check_password(data["password"]):
                                        user.login_count += 1
                                        user.save()
                                        if user.login_count == 3:
                                            user.login_attempt_time = datetime.now()
                                            user.save()
                                        return Response({
                                            "status": False,
                                            "message": f"Incorrect Password. you have only {3-user.login_count} attempts left",
                                        })
                                    else:
                                        user.login_count = 0
                                        user.login_attempt_time = None
                                        user.email_sent = True
                                        user.fcm_token = data['fcm_token']
                                        user.save()
                                        user_view = UserSerializer(user, context={'user_id':user.id})
                                        refresh = RefreshToken.for_user(user)
                                        auth.authenticate(mobile=data["mobile"], password=data["password"])
                                        auth.login(request, user)
                                        return Response({
                                            "status": True,
                                            "token": str(refresh.access_token),
                                            "refreshToken": str(refresh),
                                            "payload": user_view.data,
                                            "message": "Login Success."
                                        })  
                            else:
                                return Response( {
                                    "status": False,
                                    "message": "Mobile number not found.",
                                })
                        else:
                            return Response( {
                                "status": False,
                                "message": "Please Input validate data...",
                            })
                    else:
                        return Response( {
                            "status": False,
                            "message": "Please Input validate data...",
                        })
                else:
                    return Response( {
                        "status": False,
                        "message": "Please Input validate data...",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something went wrong!",
            })

class ChangePasswordSendMailAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=ChangePasswordEmailOTPSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = ChangePasswordEmailOTPSerializer(data=data)
                    if serializer.is_valid():
                        if User.objects.filter(email=data["email"].lower(), is_superuser=False).exists():
                            user = User.objects.get(email=data["email"].lower())
                            if user.is_verified:
                                if user.is_active:
                                    if user.otp_sent_time != None:
                                        filter_date = str(user.otp_sent_time)[:19]
                                        now_plus_5 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S" ) + timedelta(minutes=1)
                                        if datetime.now() >= now_plus_5:
                                            changePasswordOTP(user)
                                            return Response({
                                                "status": True,
                                                "message": f"OTP has been sent on {data['email'][:3]}****{data['email'].split('@')[-1]} email address.",
                                            })
                                        else:
                                            return Response({
                                                "status": False,
                                                "message": f"You can send next otp after 1 minutes. Please try after {str(now_plus_5)[11:]}.",
                                            })
                                    else:
                                        changePasswordOTP(user)
                                        return Response({
                                            "status": True,
                                            "message": f"OTP has been sent on {data['email'][:3]}****{data['email'].split('@')[-1]} email address.",
                                        })
                                else:
                                    return Response( {
                                        "status": False,
                                        "message": "Your Account is Inactive. Please contact the Admin.",
                                    })
                            else:
                                return Response( {
                                    "status": False,
                                    "message": "Email address not verified.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Email Not Found."
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please input valid data."
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input valid data."
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something went wrong!"
            })

class ChangePasswordVerifyOTPAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=ChangePasswordVerifyEmailOTPSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = ChangePasswordVerifyEmailOTPSerializer(data=data)
                    if serializer.is_valid():
                        if User.objects.filter(email=data["email"].lower(), is_superuser=False).exists():
                            user = User.objects.get(email=data["email"].lower())
                            if len(data['otp']) == 4 and data['otp'].isnumeric():
                                if user.is_verified == False:
                                    return Response({
                                        "status": False,
                                        "message": "Your Email is not verified yet.",
                                    })
                                if user.otp != data["otp"]:
                                    return Response({
                                        "status": False,
                                        "message": "OTP not matched."
                                    })
                                else:
                                    user.otp = ""
                                    user.save()
                                    return Response({
                                        "status": True,
                                        "message": "OTP successfully matched",
                                    })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "OTP must be numeric and 4 digit only."
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Email does not Exists."
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data..."
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input valid data!"
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong!"
            })

class ChangePasswordAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = ChangePasswordSerializer(data=data)
                    if serializer.is_valid():
                        if User.objects.filter(email=data["email"].lower(), is_superuser=False).exists():
                            user = User.objects.get(email=data["email"].lower())
                            if check_password(data['new_password']):
                                if user.is_verified == False or user.is_active == False:
                                    return Response({
                                        "status": False,
                                        "message": "Account not active. Please contact with Admin.",
                                    })
                                if data["new_password"] != data["confirm_password"]:
                                    return Response({
                                        "status": False,
                                        "message": "Password not match. Please try again.",
                                    })
                                else:
                                    if not user.check_password(data["confirm_password"]):
                                        user.set_password(data["confirm_password"])
                                        user.save()
                                        ip_address = get_ip()
                                        location = get_location(ip_address)
                                        sendAlert(user, location)
                                        # sendAlert(user)
                                        return Response({
                                            "status": True,
                                            "message": "Password Successfully Changed.",
                                        })
                                    else:
                                        return Response({
                                            "status": False,
                                            "message": "You can't be set old password as new password.",
                                        })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Password must be between 8 to 16 digit and must have contins @1dA.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Email Address not found."
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data..."
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input valid data!"
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something went wrong!"
            })

class MobileLoginUserAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=MobileLoginSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = MobileLoginSerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if User.objects.filter(mobile=data["mobile"], is_superuser=False).exists():
                                user = User.objects.get(mobile=data["mobile"])
                                mobile_data = user.mobile[6:10]
                                if user.is_active == False or user.is_verified == False:
                                    return Response({
                                        "status": False,
                                        "message": "Your Account is Inactive/Unverified. Please contact the Admin.",
                                    })
                                else:
                                    if user.otp_sent_time == None:
                                        if user.otp_count == str(0):
                                            user.otp_count = int(user.otp_count) + 1
                                            user.save()
                                            return Response({
                                                "status": True,
                                                "message": f"OTP send successfully on ***{mobile_data}",
                                            })
                                        elif user.otp_count < str(3):
                                            user.otp_count = int(user.otp_count) + 1
                                            if user.otp_count == 3:
                                                user.otp_sent_time = datetime.now()
                                            user.save()
                                            return Response({
                                                "status": True,
                                                "message": f"OTP send successfully on ***{mobile_data}",
                                            })
                                        else:
                                            return Response({
                                                "status": False,
                                                "message": "Your otp send request limit is over for 5 Minutes. Please try again after 5 Minutes.",
                                            })
                                    else:
                                        filter_date = str(user.otp_sent_time)[:19]
                                        now_plus_5 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=5)
                                        if datetime.now() >= now_plus_5:
                                            user.otp_count = 1
                                            user.otp_sent_time = None
                                            user.save()
                                            return Response({
                                                "status": True,
                                                "message": f"OTP send successfully on ***{mobile_data}",
                                            })
                                        else:
                                            return Response({
                                                "status": False,
                                                "message": "Your otp send request limit is over for 5 Minutes. Please try again after 5 Minutes.",
                                            })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Mobile Number not found.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile Number must be 10 digit or must be numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data...",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something went wrong.",
            })

class VerifyMobileOTPAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=MobileLoginOTPVerifySerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = MobileLoginOTPVerifySerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if User.objects.filter(mobile=data["mobile"], is_superuser=False).exists():
                                user = User.objects.get(mobile=data["mobile"])
                                if len(data['otp']) == 4 and data['otp'].isnumeric():
                                    if user.is_verified == False:
                                        return Response({
                                            "status": False,
                                            "message": "Your Account or Email not verified.",
                                        })
                                    if data["otp"] != "1234":
                                        return Response({
                                            "status": False,
                                            "message": "OTP does not match. Please try again.",
                                        })
                                    else:
                                        if user.is_active == False:
                                            user.mobile_verified = True
                                            user.save()
                                            return Response({
                                                "status": False,
                                                "in_active": True,
                                                "message": "Your Account is Inactive. Please contact the Admin",
                                            })
                                        else:
                                            user_view = UserSerializer(user)
                                            if user.mobile_verified == False:
                                                user.mobile_verified = True
                                                user.save()
                                            refresh = RefreshToken.for_user(user)
                                            return Response({
                                                "status": True,
                                                "token": str(refresh.access_token),
                                                "payload": user_view.data,
                                                "message": "Login successfully.",
                                            })
                                else:
                                    return Response({
                                        "status": False,
                                        "message": "Otp must be 4 digit and numeric only.",
                                    })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "This Mobile number not found in our system.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile Number must be 10 digit or must be numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data!.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class ResendSendMobileOTPAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=MobileNumberVerifySerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])	
                data = request.data
                if data:
                    serializer = MobileNumberVerifySerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if User.objects.filter(mobile=data["mobile"], is_superuser=False).exists():
                                if user_data.mobile == data["mobile"]:
                                    if not user_data.mobile_verified:
                                        user_mobile = user_data.mobile[6:10]
                                        if user_data.is_verified == False or user_data.is_active == False:
                                            return Response({
                                                "status": False,
                                                "message": "Your Account or Email Not verified yet.",
                                            })
                                        else:
                                            filter_date = str(user_data.otp_sent_time)[:19]
                                            now_plus_5 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
                                            if datetime.now() >= now_plus_5:
                                                user_data.otp_sent_time = datetime.now()
                                                user_data.save()
                                                # sendMobileOTP(user)
                                                return Response({
                                                    "status": True,
                                                    "message": f"OTP has been sent on last 4 ****{user_mobile} mobile number.",
                                                })
                                            else:
                                                return Response({
                                                    "status": True,
                                                    "message": f"You can send next otp after 1 minute. Please try after {str(now_plus_5)[11:]}.",
                                                })
                                    else:
                                        return Response({
                                            "status": False,
                                            "message": "Mobile number already verified!"
                                        })
                                else:
                                        return Response({
                                            "status": False,
                                            "message": "Mobile number is not associated with login user!"
                                        })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Mobile Number Not Found."
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile Number must be 10 digit or must be numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please input Valid Mobile Number.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input Valid data!"
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "This Mobile Number does not Exists."
            })

class ChangePasswordSendMobileOTPAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=MobileLoginSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = MobileLoginSerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if User.objects.filter(mobile=data["mobile"], is_superuser=False).exists():
                                user = User.objects.get(mobile=data["mobile"])
                                user_mobile = user.mobile[6:10]
                                if user.is_verified == False or user.is_active == False:
                                    return Response({
                                        "status": False,
                                        "message": "Your Account or Email Not verified yet.",
                                    })
                                else:
                                    filter_date = str(user.otp_sent_time)[:19]
                                    now_plus_5 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
                                    if datetime.now() >= now_plus_5:
                                        user.otp_sent_time = datetime.now()
                                        user.save()
                                        # sendMobileOTP(user)
                                        return Response({
                                            "status": True,
                                            "message": f"OTP has been sent on last 4 ****{user_mobile} mobile number.",
                                        })
                                    else:
                                        return Response({
                                            "status": True,
                                            "message": f"You can send next otp after 1 minute. Please try after {str(now_plus_5)[11:]}.",
                                        })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Mobile Number Not Found."
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile Number must be 10 digit or must be numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please input Valid Mobile Number.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input Valid data!"
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "This Mobile Number does not Exists."
            })

class ChangePasswordMobileOTPVerifyAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=MobileLoginOTPVerifySerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = MobileLoginOTPVerifySerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if User.objects.filter(mobile=data["mobile"], is_superuser=False).exists():
                                user = User.objects.get(mobile=data["mobile"])
                                if len(data['otp']) == 4 and data['otp'].isnumeric():
                                    if user.is_verified == False:
                                        return Response({
                                            "status": False,
                                            "message": "Your Email is not verified yet.",
                                        })
                                    if data["otp"] != "1234":
                                        return Response({
                                            "status": False,
                                            "message": "OTP not matched."
                                        })
                                    else:
                                        return Response({
                                            "status": True,
                                            "message": "OTP successfully matched",
                                        })
                                else:
                                    return Response({
                                        "status": False,
                                        "message": "Otp must be 4 digit and numeric only.",
                                    })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Mobile Number does not Exists.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile Number must be 10 digit or must be numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data..."
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input valid data!"
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong!"
            })

class ChangePasswordMobileAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=ChangePasswordMobileSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = ChangePasswordMobileSerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if User.objects.filter(mobile=data["mobile"], is_superuser=False).exists():
                                user = User.objects.get(mobile=data["mobile"])
                                if check_password(data['new_password']):
                                    if user.is_verified == False or user.is_active == False:
                                        return Response({
                                            "status": False,
                                            "message": "Account not active. Please contact with Admin.",
                                        })
                                    if data["new_password"] != data["confirm_password"]:
                                        return Response({
                                            "status": False,
                                            "message": "Password not match. Please try again.",
                                        })
                                    else:
                                        if not user.check_password(data["confirm_password"]):
                                            user.set_password(data["confirm_password"])
                                            user.save()
                                            sendAlert(user)
                                            return Response({
                                                "status": True,
                                                "message": "Password Successfully Changed.",
                                            })
                                        else:
                                            return Response({
                                                "status": False,
                                                "message": "You can't be set old password as new password.",
                                            })
                                else:
                                    return Response({
                                        "status": False,
                                        "message": "Password must be between 8 to 16 digit and must have contins @1dA.",
                                    })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Mobile Number does not Exists.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile Number must be 10 digit or must be numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data..."
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input valid data!"
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something went wrong!"
            })

class MobileNumberVerifyAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=MobileNumberVerifySerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = MobileNumberVerifySerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if not User.objects.filter(mobile=data["mobile"]).exclude(id=user_data.id).exists():
                                #call otp send function
                                if user_data.mobile_verified:
                                    return Response({
                                        "status": False,
                                        "message": "Mobile number already verfied.",
                                    })
                                return Response({
                                    "status": True,
                                    "message": "OTP has been sent on this mobile number.",
                                })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Mobile Already used.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile number must be 10 digit and numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data!.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class MobileNumberOTPVerifyAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=MobileNumberOTPVerifySerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = MobileNumberOTPVerifySerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if not User.objects.filter(mobile=data["mobile"]).exclude(id=user_data.id).exists():
                                if len(data['otp']) == 4 and data['otp'].isnumeric():
                                    if user_data.mobile_verified:
                                        return Response({
                                            "status": False,
                                            "message": "Mobile number already verfied.",
                                        })
                                    if data['otp'] == '1234':
                                        user_data.mobile_verified = True
                                        user_data.save()
                                        user_serializer = UserSerializer(user_data).data
                                        return Response({
                                            "status": True,
                                            'payload':user_serializer,
                                            "message": "Mobile number successfully verified.",
                                        })
                                    else:
                                        return Response({
                                            "status": False,
                                            "message": "OTP not matched.",
                                        })
                                else:
                                    return Response({
                                            "status": False,
                                            "message": "OTP must be 4 digit and numeric only.",
                                        })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Mobile Already used.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile number must be 10 digit and numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data!.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class PasswordResetAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=PasswordResetSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = PasswordResetSerializer(data=data)
                    if serializer.is_valid():
                        if not user_data.check_password(data['current_password']):
                            return Response({
                                "status": False,
                                "message": "Current password not matched!",
                            })
                        if data['new_password'] != data['confirm_password']:
                            return Response({
                                "status": False,
                                "message": "New password and Confirm password not matched!",
                            })
                        if not check_password(data['confirm_password']):
                            return Response({
                                "status": False,
                                "message": "Password must be between 8 to 16 digit and must have contins @1dA.",
                            })
                        if user_data.check_password(data['confirm_password']):
                            return Response({
                                "status": False,
                                "message": "New password not be old password.",
                            })
                        else:
                            user_data.set_password(data['confirm_password'])
                            user_data.save()
                            return Response({
                                "status": True,
                                "message": "Password Changed!",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please input valid data.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input valid data.",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class AddressAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                address_id = self.request.query_params.get("address_id")
                pagination = PageNumberPagination()
                pagination.page_size = GLOBAL_PAGINATION_RECORD
                pagination.page_size_query_param = "page_size"
                if not address_id:
                    address = Address.objects.filter(user_id=user_data.id).order_by('-id')
                    address_pagination = pagination.paginate_queryset(address, request)
                    address_serializer = AddressSerializer(address_pagination, many=True).data
                    pagination_record = pagination.get_paginated_response(address_serializer).data
                    return Response({
                        "status": True,
                        "payload": pagination_record,
                        "message": "All address fetched.",
                    })
                else:
                        if Address.objects.filter(user_id=user_data.id, id=address_id).exists():
                            address = Address.objects.get(id=address_id)
                            if address:
                                address_serializer = AddressSerializer(address).data
                                return Response({
                                    "status": True,
                                    "payload": address_serializer,
                                    "message": "address fetched.",
                                })
                            else:
                                return Response({
                                    "status": True,
                                    "message": "Invalid Request.",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "No address found.",
                            })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=AddressSerializer)
    def post(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            address_id = self.request.query_params.get("address_id")
            data = request.data
            if data:      
                serializer = AddressSerializer(data=data)
                if not serializer.is_valid():
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!",
                    })
                elif not address_id:
                    if (len(data["phone_number"]) == 10 and data["phone_number"].isnumeric()):
                        if data['is_default'] == "1":
                            if Address.objects.filter(user_id=user_data.id, is_default=1).exists():
                                address = Address.objects.get(user_id=user_data.id, is_default=1)
                                address.is_default = False
                                address.save()
                                serializer.save(user_id=user_data.id)
                                return Response({
                                    "status": True,
                                    "message": "Address added.",
                                })
                        serializer.save(user_id=user_data.id)
                        return Response({
                            "status": True,
                            "message": "Address added.",
                        })
                    else:
                        return Response({
                            "status": False,
                            "message": "Mobile number must be 10 digit and numeric only.",
                        })
                else:
                    if not Address.objects.filter(user_id=user_data.id, id=address_id).exists():
                        return Response({
                                "status": False,
                                "message": "Address Not Found.",
                            })
                    elif (len(data["phone_number"]) != 10 and not data["phone_number"].isnumeric()):
                        return Response({
                            "status": False,
                            "message": "Mobile number must be 10 digit and numeric only.",
                        })
                    elif data['is_default'] == "1":
                        address = Address.objects.filter(user_id=user_data.id, is_default=1)
                        if not address.exists():
                            return Response({
                                "status": False,
                                "message": "At least one address must be default. Please Select False.",
                            })
                        address = address.first()
                        address.is_default = False
                        address.save()
                    update_address = Address.objects.get(id=address_id)
                    if data['is_default'] == "1":
                        update_address.is_default = True
                    update_address.address_title = data['address_title']
                    update_address.address = data['address']
                    update_address.area = data['area']
                    update_address.city = data['city']
                    update_address.state = data['state']
                    update_address.zipcode = data['zipcode']
                    # update_address.landmark = data['landmark']
                    update_address.phone_number = data['phone_number']
                    update_address.calling_code = data['calling_code']
                    update_address.country_code = data['country_code']
                    update_address.save()
                    return Response({
                        "status": True,
                        "message": "Address updated.",
                    })

            else:
                return Response({
                    "status": False,
                    "message": "Please Input validate data!.",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=AddressSerializer)
    def delete(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            address_id = self.request.query_params.get("address_id")
            if address_id:
                user_address = Address.objects.filter(user_id=user_data.id)
                if user_address.exists():
                    address = Address.objects.get(id=address_id)
                    if address.is_default == True:
                        if Address.objects.filter(user_id=user_data.id).exclude(id=address_id).count() == 1:
                            all_address = user_address.filter(is_default=False).first()
                            all_address.is_default = True
                            all_address.save()
                            user_address.filter(id=address_id).delete()
                            return Response({
                                "status": True,
                                "message": "Address deleted.",
                            })
                        else:
                            user_address.filter(id=address_id).delete()
                            return Response({
                                "status": True,
                                "message": "Address deleted.",
                            })
                    else:    
                        user_address.filter(id=address_id).delete()
                        return Response({
                            "status": True,
                            "message": "Address deleted.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Address not found!",
                    })
            else:
                return Response({
                    "status": False,
                    "message": "Please enter valid address ID.",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class AppIntroAPI(APIView):
    parser_classes = [JSONParser]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                intro = AppIntro.objects.all().order_by('-id')
                intro_serializer = AppIntroSerializer(intro, many=True).data
                return Response({
                    "status": True,
                    "payload": intro_serializer,
                    "message": "All Intro Screen fetched.",
                })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class ContactUsAPI(APIView):
    parser_classes = [JSONParser]
    @swagger_auto_schema(request_body=ContactUsSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = request.data
                if data:
                    serializer = ContactUsSerializer(data=data)
                    if serializer.is_valid():
                        serializer.save()
                        sendQuery(data['name'], data['email'], data['message'], data['subject'], datetime.now())
                        return Response({
                            "status": True,
                            "message": "We have received for query. Please wait for the response.",
                        })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input validate data!.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class ProfileAPI(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=ProfileSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = ProfileSerializer(data=data)
                    if serializer.is_valid():
                        if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                            if check_ssn(data['social_security_number']):
                                user_data.name = data['name']
                                if 'profile_pic' in data:
                                    user_data.profile_pic =  data.get('profile_pic')
                                if User.objects.filter(mobile=data['mobile'], mobile_verified=True).exclude(id=data1['user_id']).exists():
                                    return Response({
                                        "status": False,
                                        "message": "Mobile number is already verified with another account.",
                                    })
                                user_data.calling_code = data['calling_code']
                                user_data.country_code = data['country_code']
                                user_data.social_security_number = data['social_security_number']
                                if user_data.mobile != data['mobile']:
                                    user_data.mobile = data['mobile']
                                    user_data.mobile_verified = False
                                user_data.save()
                                user = User.objects.get(id = data1['user_id'])
                                profile_serializer = UserSerializer(user).data
                                return Response({
                                    "status": True,
                                    'payload': profile_serializer,
                                    "message": "Profile updated.",
                                })
                            else:
                                return Response({
                                    'status': False,
                                    'message': 'Invalid SSN.',
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Mobile Number must be 10 digit or must be numeric only.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please input valid data.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input valid data.",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class NotificationSettingsAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=NotificationSettingsSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = NotificationSettingsSerializer(data=data)
                    if serializer.is_valid():
                        if data['notification'] == "1" or data['notification'] == "0":
                            user_data.notification_settings = int(data['notification'])
                            user_data.save()
                            user_serializer = UserSerializer(user_data).data
                            return Response({
                                "status": True,
                                'payload': user_serializer,
                                "message": "Notification settings updated.",
                            })
                        else:
                            return Response({
                                "status": False,
                                "message": "Notification type must be boolean.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please input valid data.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Please input valid data.",
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class LogoutAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                user_data.fcm_token = None
                user_data.save()
                auth.logout(request)
                return Response({
                    "status": True,
                    "message": "Logout successfully.",
                })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class ContactListAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                pagination = PageNumberPagination()
                pagination.page_size = GLOBAL_PAGINATION_RECORD
                pagination.page_size_query_param = "page_size"
                contact_list = ContactList.objects.filter(user_id=user_data.id).order_by('-id')
                contact_pagination = pagination.paginate_queryset(contact_list, request)
                serializer = ContactListSerializer(contact_pagination, many=True).data
                pagination_record = pagination.get_paginated_response(serializer).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "Contact list fetched.",
                })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=ContactListSerializer)
    def post(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            data = request.data
            if data:
                serializer = ContactListSerializer(data=data)
                if serializer.is_valid():
                    ContactList.objects.filter(user_id=user_data.id).delete()
                    contact_list = []
                    for i in data['contactList[]']:
                        contact_list.append(ContactList(user_id=user_data.id, name=i['name'], mobile_number=i['mobile_number']))
                    ContactList.objects.bulk_create(contact_list)
                    return Response({
                        "status": True,
                        "message": "Contact Saved.",
                    })
                else:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    })
            else:
                return Response({
                    "status": False,
                    "message": "Please Input validate data!.",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class SideMenuListAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                return Response({
                    "status": True,
                    "payload": side_menu,
                    "message": "Side menu list fetched.",
                })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class UserInfoAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=UserInformationSerializer)
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                if not user_data.is_active and not user_data.is_verified:
                    return Response({
                        "status": False,
                        "message": "Unauthenticated User!",
                    })
                data = request.data
                if not data:
                    return Response({
                        'status': False,
                        'message': 'Please input valid data.'
                    })
                serializer = UserInformationSerializer(data=data)
                if not serializer.is_valid():    
                    return Response({
                    'status': False,
                    'message': 'Please input valid data.'
                })
                try:
                    user_information = User.objects.get(slug_user=data['slug'])
                    profile_serializer = UserInformationSerializer(user_information).data
                    return Response({
                        "status": True,
                        'payload': profile_serializer,
                        "message": "User information fetched successfully.",
                    })
                except User.DoesNotExist:
                    return Response({
                        'status': False,
                        'message': 'Invalid user.'
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class StatesAPI(APIView):
    def get(self, request):
        try:
            try:
                json_data = open("states.json")
                states_data = json.load(json_data)
                return Response({
                    "status": True,
                    'payload': states_data,
                    "message": "States code fetched.",
                })
            except:
                return Response({
                    'status': False,
                    'message': 'Server not responding.'
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })