from django.contrib.auth.models import auth
from django.conf import settings
from superadmin.models import *
from .serializers import *
from api.auth_api.serializers import UserSerializer
from rest_framework.pagination import PageNumberPagination
import re
from api.fake_email import *
from .email import *
from django.core.exceptions import ValidationError
from api.utils import *
from api.jwt import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg
import jwt
import stripe
import json
from api.utils import *
from django.db.models import Q
from api.status_code import *
from django.db import transaction, IntegrityError
from superadmin.choices import BUSINESS_TYPE
from datetime import datetime, timedelta
from api.dwolla_payment import check_wallet_amount
from api.dwolla_payment import DwollaTransferAPI
from dwollav2.error import Error as DwollaError
import threading
from api.custom_threading import threaded_function

def check_password(password):
    return bool(re.match('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).{8,16}$', password))==True

class StoreRegisterAPI(APIView):
    #create a function for the store registration.
    parser_classes = [MultiPartParser]
    def post(self, request):
        try:
            data = request.data
            if data:
                serializer = StoreRegisterSerializer(data=data)
                if (BlockEmailDomain.objects.filter(domain__contains=data['email'].split('@')[1], is_active=True) or data['email'].split('@')[1] in fake_email_list):
                    return Response({
                        'status': False,
                        'message': 'Email address not acceptable.',
                    },
                    HTTP_406_NOT_ACCEPTABLE
                    )
                if User.objects.filter(email=data['email'].lower()).exists():
                    return Response({
                        'status': False,
                        'message': 'This Email address already registered.',
                    },
                    HTTP_409_CONFLICT
                    )
                if not serializer.is_valid(raise_exception=False):
                    return Response({
                        'status': False,
                        'message': serializer.errors,
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if User.objects.filter(mobile=data['mobile']).exists():
                    return Response({
                        'status': False,
                        'message': 'Mobile Number must be unique.',
                    },
                    HTTP_409_CONFLICT
                    )
                if len(data['mobile']) != 10 or not data['mobile'].isnumeric():
                    return Response({
                        'status': False,
                        'message': 'Mobile number must be numeric and 10 digit',
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if (data['profile_pic'].name.split('.')[-1]).lower() in img_type:
                    if not get_size(data['profile_pic']):
                        return Response({
                            'status': False,
                            'message': 'Image size must be less than 5 MB.',
                        },
                        HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        )
                    if not check_ssn(data['social_security_number']):
                        return Response({
                            'status': False,
                            'message': 'SSN must be valid or 9 digit only.',
                        },
                        HTTP_400_BAD_REQUEST
                        )
                    if not check_ein(data['ein_number']):
                        return Response({
                            'status': False,
                            'message': 'Employer Identification Number(EIN) must be valid or 9 digit only.',
                        },
                        HTTP_400_BAD_REQUEST
                        )
                    store_tier = tier_selection(data['avg_ticket'])
                    if not store_tier:
                        return Response({
                            'status': False,
                            'message': 'Tier not found.',
                        },
                        HTTP_404_NOT_FOUND
                        )
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
                        "dateOfBirth": data.get('dob', ''),
                        "ssn": data.get('social_security_number', ''),
                        }
                        user = User(email=data['email'].lower(), mobile=data['mobile'],
                        profile_pic=data['profile_pic'], country_code=data['country_code'], name=data['firstName']+' '+data['lastName'], 
                        calling_code=data['calling_code'], is_store=1, social_security_number=data['social_security_number'], 
                        document=data['document']) 
                        user.set_password(data['password'])
                        user.save_with_slug()
                        StoreProfile.objects.create(user_id=user.id, dob=data['dob'], store_name=data['store_name'], address=data['address'], 
                        tax_id=data['ein_number'].upper(),
                        business_type=data['business_type'], avg_amount=store_tier.end_price, interval_month=store_tier.interval_month,
                        interest=store_tier.interest)
                        sendOTP(user, data['store_name'])
                        StoreTiming.objects.create(user_id=user.id)
                        t = threading.Thread(target=threaded_function, args=(customer_data,user.id))
                        t.start()
                        return Response({
                            'status': True,
                            'message': 'Verification code sent on the mail address. Please check',
                        },
                        HTTP_201_CREATED
                        )
                    except IntegrityError as e:
                        return Response({
                            'status': False,
                            'message': e,
                        })
                    except ValidationError as error:
                        return Response({
                            'status': False,
                            'message': error,
                        })
                    except DwollaError as e:
                        return Response(
                            {
                                'status':False,
                                'message': e.body['_embedded']['errors'][0]['message']
                            },
                            e.status
                            ) 
                    except:
                        return Response({
                            'status': False,
                            'message': 'Dwolla facing huge traffic now. Please try again.',
                        })
                else:
                    return Response({
                        'status': False,
                        'message': 'Image type must be png,jpeg only.',
                    },
                    HTTP_400_BAD_REQUEST
                    )
            else:
                return Response({
                    'status': False,
                    'message': 'Please input valid data.'
                },
                HTTP_400_BAD_REQUEST
                )
        except:
            return Response({
                'status': False,
                'message': 'Something went wrong!'
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

class StoreProfileAPI(APIView):
    #create a function for the store profile view.
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
                store_id = self.request.query_params.get("store_id")
                store_rating = self.request.query_params.get("store_rating")
                store_name = self.request.query_params.get("store_name")
                store_address = self.request.query_params.get("store_address")
                queryset = Q()  # for all queries
                if store_rating:
                    if store_rating == "high":
                        store_rating = "-rating"
                    if store_rating == "low":
                        store_rating = "rating"
                else:
                    store_rating = "-id"
                if store_id:
                    queryset &= Q(user__id=store_id)
                if store_address:
                    queryset &= Q(address__contains=store_address)
                if store_name:
                    queryset &= Q(store_name__contains=store_name)
                if user_data.is_verified and user_data.is_active:
                    store = StoreProfile.objects.filter(user__is_active=True).filter(queryset).order_by(f'{store_rating}')
                    store_pagination = pagination.paginate_queryset(store, request)
                    store_serializer = StoreProfileSerializer(store_pagination, many=True, context={'user':user_data.id}).data
                    pagination_record = pagination.get_paginated_response(store_serializer).data
                    return Response({
                        'status': True,
                        'payload': pagination_record,
                        'message': 'All store profile fetched.'
                    })
                else:
                    return Response({
                        'status': False,
                        'message': 'Unauthenticated User!'
                    })
            else:
                return Response({
                    'status': False,
                    'message': 'Content type must be in application/json'
                })
        except:
            return Response({
                'status': False,
                'message': 'Something went wrong!'
            })

    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            data = request.data
            if data:
                serializer = StorePersonalProfileSerializer(data=data)
                if serializer.is_valid():
                    if (len(data["mobile"]) == 10 and data["mobile"].isnumeric()):
                        if check_ssn(data['social_security_number']):
                            if User.objects.filter(mobile=data['mobile'], mobile_verified=True).exclude(id=data1['user_id']).exists():
                                return Response({
                                    "status": False,
                                    "message": "Mobile number is already verified with another account.",
                                })
                            store = StoreProfile.objects.get(user_id=user_data.id)
                            user_data.calling_code = data['calling_code']
                            user_data.country_code = data['country_code']
                            user_data.social_security_number = data['social_security_number']
                            if user_data.mobile != data['mobile']:
                                user_data.mobile = data['mobile']
                                user_data.mobile_verified = False
                            if 'profile_pic' in data:
                                user_data.profile_pic =  data.get('profile_pic')
                            user_data.name = data['owner_name']
                            user_data.save()
                            store.about_us = data['about_us']
                            store.store_name = data['store_name']
                            store.address = data['address']
                            store.tax_id = data['ein_number']
                            store.business_type = data['business_type']
                            store.dob = data['dob']
                            store.save()
                            StoreTiming.objects.filter(user_id=user_data.id).update(timing=data['store_timing'])
                            store_data = User.objects.get(id = data1['user_id'])
                            profile_serializer = UserSerializer(store_data).data
                            return Response({
                                "status": True,
                                'payload': profile_serializer,
                                "message": "Profile updated.",
                            })
                        else:
                            return Response({
                                'status': False,
                                'message': 'SSN must be valid or 9 digit only.',
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
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class StoreRatingAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            data = request.data
            if not data:
                return Response({
                    "status": False,
                    "message": "Please Input validate data!.",
                })
            serializer = StoreRatingSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data!.",
                })
            if not StoreProfile.objects.filter(user_id=data['store_id']).exists():
                return Response({
                    "status": False,
                    "message": "Invalid Store ID.",
                })
            if StoreRating.objects.filter(user_id=user_data.id, store_id=data['store_id']).exists():
                return Response({
                    "status": False,
                    "message": "You have already submitted rating.",
            })
            if not data['rating'] <= 5 and not data['rating'] > 0: 
                return Response({
                    "status": False,
                    "message": "Rating must be between 1 to 5.",
                })
            StoreRating.objects.get_or_create(user_id=user_data.id, store_id=data['store_id'], 
            rating=data['rating'], review=data['review'])
            store_rating = StoreRating.objects.filter(store_id=data['store_id']).aggregate(Avg('rating'))
            store_profile = StoreProfile.objects.get(user_id=data['store_id'])
            store_profile.rating = store_rating['rating__avg']
            store_profile.save()
            return Response({
                "status": True,
                "message": "Store rating updated.",
            })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class StoreAvgTicketAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = StoreAvgTicketSerializer(data=data)
                    if serializer.is_valid():
                        if StoreProfile.objects.filter(user_id=user_data.id).exists():
                            store = StoreProfile.objects.get(user_id=user_data.id)
                            if float(data['avg_amount']) > 0 and int(data['loan_tenure']) > 0 and float(data['surcharge']) > 0:
                                store.avg_amount = data['avg_amount']
                                store.interest = data['surcharge']
                                store.interval_month = data['loan_tenure']
                                store.save()
                                return Response({
                                    "status": True,
                                    "message": "Ticket updated.",
                                })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Please enter valid data!",
                                })
                        else:
                            return Response({
                                "status": False,
                                "message": "Store not found!",
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

class StoreBusinessAPI(APIView):
    #create a function for the store profile view.
    parser_classes = [JSONParser]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data = []
                for i in BUSINESS_TYPE:
                    data.append(i[0])
                return Response({
                    'status': True,
                    'payload': data,
                    'message': 'All business fetched.'
                })
            else:
                return Response({
                    'status': False,
                    'message': 'Content type must be in application/json'
                })
        except:
            return Response({
                'status': False,
                'message': 'Something went wrong!'
            })
        
class StoreLoanAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                user_type = request.query_params.get("user_type")
                if user_type not in ['STORE', 'BORROWER']:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                queryset = Q()  # for all queries
                if user_type == "STORE":
                    queryset &= Q(store_id=user_data.id)
                if user_type == "BORROWER":
                    queryset &= Q(user_id=user_data.id)
                store_data = StoreLoanEmi.objects.filter(queryset).order_by('-id')
                serializer = StoreLoanViewSerializer(store_data, many=True).data
                return Response({
                    'status': True,
                    'payload': serializer,
                    'message': 'Loan Request fetched.'
                },
                HTTP_200_OK
                )
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                },
                HTTP_400_BAD_REQUEST
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if not data:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                serializer = StoreLoanSerializer(data=data)
                if not serializer.is_valid():
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if not User.objects.filter(id=user_data.id, is_store=1).exists():
                    return Response({
                        "status": False,
                        "message": "Unauthorized user!",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
                if data['loan_type'] not in ['CASH', 'PRODUCT']:
                    return Response({
                        "status": False,
                        "message": "Please select valid loan type.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if type(data['amount']) != int and data['amount'] > 100:
                    return Response({
                        "status": False,
                        "message": "Please enter valid amount.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if not User.objects.filter(id=data['user_id'], is_store=False).exclude(id=user_data.id).exists():
                    return Response({
                        "status": False,
                        "message": "User not found!",
                    },
                    HTTP_204_NO_CONTENT
                    )
                if StoreLoanEmi.objects.filter(user_id=data['user_id'], store_id=user_data.id, approve=0).exists():
                    return Response({
                        "status": False,
                        "message": "Request is already pending!",
                    },
                    HTTP_409_CONFLICT
                    )
                store_tier = StoreTier.objects.filter(end_price__gte=data['amount'], starting_price__lte=data['amount']).first()
                if not store_tier:
                    return Response({
                        "status": False,
                        "message": "No Tier found. Please enter a valid amount.",
                    },
                    HTTP_204_NO_CONTENT
                    )
                if not LenderWallet.objects.filter(user_id=user_data.id).exists():
                    return Response({
                        "status": False,
                        "message": "Please add bank first."
                    })
                lender_wallet = LenderWallet.objects.get(user_id=user_data.id)
                if not check_wallet_amount(wallet_id=lender_wallet.wallet_id, amount=data['amount']):
                    return Response({
                        "status": False,
                        "message": "You have insufficient balance in your wallet."
                    })
                time_limit = datetime.strptime(str(datetime.now())[:19], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
                StoreLoanEmi.objects.create(user_id=data['user_id'], store_id=user_data.id, amount=data['amount'], 
                                            tenure=store_tier.interval_month, fee=store_tier.interest, loan_type=data['loan_type'], time_limit=time_limit)
                return Response({
                    'status': True,
                    'message': 'Loan Request sent.'
                },
                HTTP_201_CREATED
                )
                
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                },
                HTTP_400_BAD_REQUEST
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class StoreLoanRequestAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if not data:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                serializer = StoreLoanRequestSerializer(data=data)
                if not serializer.is_valid():
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if not User.objects.filter(id=user_data.id, is_store=0).exists():
                    return Response({
                        "status": False,
                        "message": "Unauthorized user!",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
                if data['request_type'] not in ['ACCEPT', 'REJECT']:
                    return Response({
                        "status": False,
                        "message": "Please select valid a valid request type.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if not StoreLoanEmi.objects.filter(user_id=user_data.id, id=data['loan_id']).exists():
                    return Response({
                        "status": False,
                        "message": "No request found!",
                    },
                    HTTP_204_NO_CONTENT
                    )
                store_emi = StoreLoanEmi.objects.get(id=data['loan_id'])
                time_limit = datetime.strptime(str(store_emi.time_limit)[:19], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
                if datetime.now() > time_limit:
                    return Response({
                        'status': False,
                        'message': 'Time limit exceed.'
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if data['request_type'] == 'ACCEPT':
                    lender_wallet = LenderWallet.objects.get(user_id=store_emi.store_id)
                    borrower_wallet = LenderWallet.objects.get(user_id=user_data.id)
                    with transaction.atomic():
                        try:
                            request_data = {
                                'id':store_emi.id,
                                'funding_source': lender_wallet.wallet_id,
                                'destination_source': borrower_wallet.wallet_id,
                                'amount': store_emi.amount,
                                'message': f"Amount Transfer by {store_emi.store.name}"
                            }
                            DwollaTransferAPI.create_transfer(request_data)
                            store_emi.approve = True
                            store_emi.approve_date = datetime.now()
                            store_emi.save()
                            return Response({
                                'status': True,
                                'message': 'Loan Request accepted.'
                            },
                            HTTP_200_OK
                            ) 
                        except DwollaError as e:
                            return Response(
                                {
                                    'status':False,
                                    'message': e.body['message']
                                },
                                e.status
                            )  
                if data['request_type'] == 'REJECT':
                    store_emi.delete()
                    return Response({
                        'status': True,
                        'message': 'Loan Request rejected.'
                    },
                    HTTP_200_OK
                    )       
            else:
                return Response({
                    'status': False,
                    'message': 'Accept type must be in application/json.'
                },
                HTTP_400_BAD_REQUEST
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )