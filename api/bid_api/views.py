from api.auth_api.serializers import UserInformationSerializer
from django.contrib.auth.models import auth
from superadmin.models import *
from superadmin.choices import *
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from .serializers import *
from django.db import transaction, IntegrityError
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle
import json
from .email import *
from api.utils import *
from api.jwt import *
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
import jwt
from api.dwolla_payment import check_wallet_amount
from api.dwolla_payment import DwollaTransferAPI
from dwollav2.error import Error as DwollaError
import threading
from api.push_notifications import push_notification

class BorrowerAmountRequestAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            request_id = self.request.query_params.get("request_id")
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            user_type = request.query_params.get("user_type", None)
            queryset = Q()
            # if user_type not in ['LENDER', 'BORROWER', 'LENDING_BOX']:
            #     return Response({
            #         "status": False,
            #         "message": "Please select a valid user type!",
            #     })
            if BorrowerRequestAmount.objects.filter(user_id=user_data.id, id=request_id).exists():
                return Response({
                    "status": False,
                    "message": "No Request found.",
                })
            if user_data.is_active and user_data.is_verified:
                if user_type == "LENDER":
                    queryset &= Q(lender_id=user_data.id)
                if user_type == 'BORROWER':
                    queryset &= Q(user_id=user_data.id)
                if user_type == 'LENDING_BOX':
                    queryset &= Q(user_id=user_data.id)
                amount_request = BorrowerRequestAmount.objects.filter(queryset, approve=0).order_by('-id')
                product_pagination = pagination.paginate_queryset(amount_request, request)
                amount_serializer = BorrowerAmountRequestListSerializer(product_pagination, many=True, context={'user':user_data.id, 'user_type':user_type}).data
                pagination_record = pagination.get_paginated_response(amount_serializer).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "All request fetched.",
                })
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

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
            serializer = BorrowerAmountRequestSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data!.",
                })
            if not user_data.is_active and not user_data.is_verified:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!.",
                })
            if data['request_type'] not in ['DIRECT', 'BID']:
                return Response({
                    "status": False,
                    "message": "Request type must be valid.",
                })
            loan_management = LoanManagement.objects.first()
            if (loan_management and float(data['amount']) > float(loan_management.amount)) or not float(data['amount']) >= 100:
                return Response({
                    "status": False,
                    "message": f"Amount must be valid or greater than $100 and less than ${loan_management.amount}.",
                })
            if (loan_management and float(data['fee']) > float(loan_management.interest)) or not float(data['fee']) > 0:
                return Response({
                    "status": False,
                    "message": f"Fee must be greater than 1 and less than {loan_management.interest}.",
                })
            if not int(data['tenure']) >= 1 and int(data['tenure']) <= loan_management.tenure_month:
                return Response({
                    "status": False,
                    "message": f"Tenure must be between 1 to {loan_management.tenure_month} months.",
                })
            if not LenderWallet.objects.filter(user_id=user_data.id).exists():
                return Response({
                    "status": False,
                    "message": "Please setup account first.",
                })
            if data['request_type'] == 'DIRECT':
                if BorrowerRequestAmount.objects.filter(user_id=user_data.id, approve=0, reject=0).exists():
                    return Response({
                        "status": False,
                        'message': "Your Request is already pending."
                    }) 
                request_sent = False
                for i in json.loads(data['lenderList']):
                    if i != user_data.id:
                        if LenderWallet.objects.filter(user_id=i).exists():
                            if not BorrowerRequestAmount.objects.filter(user_id=user_data.id, lender_id=i, approve=0).exists():
                                BorrowerRequestAmount.objects.create(user_id=user_data.id, amount=data['amount'], 
                                request_type=data['request_type'], fee=data['fee'], tenure=data['tenure'], lender_id=i)
                                request_sent = True
                if request_sent:
                    return Response({
                        "status": True,
                        'message': "Request Raised.",
                    })   
                else:
                    return Response({
                        "status": False,
                        'message': "Please setup account first.",
                    })
            if data['request_type'] == 'BID':
                if BorrowerRequestAmount.objects.filter(user_id=user_data.id, approve=0).exists():
                    return Response({
                        "status": False,
                        'message': "Your Request is already pending.",
                    })  
                all_lenders = User.objects.filter(is_superuser=False, is_active=True, is_verified=True).exclude(id=user_data.id)
                bid_request_id = BidRequest.objects.create(borrower_id=user_data.id, amount=data['amount'], fee=data['fee'], tenure=data['tenure'])
                for i in all_lenders:
                    if LenderWallet.objects.filter(user_id=i).exists():
                        message_title = "New Bid Request found"
                        message_body =  f'{user_data.name} raised new bid request'
                        payload = {
                            'push_type': "bid_request",
                            'data': {
                            'name': user_data.name,
                            'profile_pic': user_data.profile_pic.url if user_data.profile_pic else None,
                            'amount':data['amount'],
                            'fee':data['fee'],
                            'tenure':data['tenure'],
                            'bid_id':bid_request_id.id
                            }
                        }
                        if i.fcm_token:
                            thread = threading.Thread(target=push_notification, args=(i.fcm_token, message_title, message_body, payload))
                            thread.start()
                        BorrowerRequestAmount.objects.create(user_id=user_data.id, amount=data['amount'], 
                        request_type=data['request_type'], fee=data['fee'], tenure=data['tenure'], lender_id=i.id, bid_id=bid_request_id.id)
                return Response({
                    "status": True,
                    'message': "Request Raised.",
                })                                                                    
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            request_id = self.request.query_params.get("request_id")
            if user_data.user_type == 'BORROWER' and user_data.is_active == True:
                if request_id:
                    if BorrowerRequestAmount.objects.filter(user_id=user_data.id).exists():
                        BorrowerRequestAmount.objects.filter(user_id=user_data.id, id=request_id, approve=0).delete()
                        return Response({
                            'success': True, 
                            'message': 'Request deleted.'
                        })
                    else:
                        return Response({
                            'success': False, 
                            'message': 'Request not found!'
                        })
                else:
                    return Response({
                        'success': False, 
                        'message': 'Please enter valid request ID!'
                    })
            else:
                return Response({
                    'success': False, 
                    'message': 'Unauthenticated user!'
                })
        except:
            return Response({
                'success': False, 
                'message': 'Something went wrong!'
            })

class LenderLoansRequestAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            request_id = self.request.query_params.get("request_id")
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            if user_data.is_active and user_data.is_verified:
                if not request_id:
                    amount_request = BorrowerRequestAmount.objects.filter(lender_id=user_data.id, approve=0, reject=0).order_by('-id')
                    product_pagination = pagination.paginate_queryset(amount_request, request)
                    amount_serializer = LenderViewRequestSerializer(product_pagination, many=True).data
                    pagination_record = pagination.get_paginated_response(amount_serializer).data
                    return Response({
                        "status": True,
                        "payload": pagination_record,
                        "message": "All request fetched.",
                    })
                else:
                    if BorrowerRequestAmount.objects.filter(lender_id=user_data.id, id=request_id).exists():
                        borrower_request = BorrowerRequestAmount.objects.get(id=request_id)
                        if borrower_request:
                            amount_serializer = BorrowerAmountRequestViewSerializer(borrower_request).data
                            return Response({
                                "status": True,
                                "payload": amount_serializer,
                                "message": "Request fetched.",
                            })
                        else:
                            return Response({
                                "status": True,
                                "message": "Invalid Request.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "No request found.",
                        })
            else:
                return Response({
                    "status": False,
                    "message": "Account not Active!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            data = request.data
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    })
            serializer = LenderSendAmountSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    })
            if not user_data.is_active and not user_data.is_verified:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!.",
                })
            if not BorrowerRequestAmount.objects.filter(id=data['request_id']).exists():
                return Response({
                    "status": False,
                    "message": "No request found with this id.",
                })
            borrower_request = BorrowerRequestAmount.objects.get(id=data['request_id'])
            if not LenderWallet.objects.filter(user_id=user_data.id).exists():
                return Response({
                    "status": False,
                    "message":  "Account not found!"
                }) 
            if data['approve_type'] == 'False':
                borrower_request.reject = True
                borrower_request.save()
                return Response({
                    "status": True,
                    "message": "Request Rejected."
                })
            lender_wallet = LenderWallet.objects.get(user_id=user_data.id)
            if not check_wallet_amount(wallet_id=lender_wallet.wallet_id, amount=borrower_request.amount):
                return Response({
                    "status": False,
                    "message": "You have insufficient balance in your wallet."
                })
            borrower_wallet = LenderWallet.objects.get(user_id=borrower_request.user_id)
            with transaction.atomic():
                try:
                    request_data = {
                        'id':borrower_request.id,
                        'funding_source':lender_wallet.wallet_id,
                        'destination_source':borrower_wallet.wallet_id,
                        'amount':borrower_request.amount,
                        'message': f"Amount Transfer by {borrower_request.lender.name}"
                    }
                    DwollaTransferAPI.create_transfer(request_data)
                    borrower_request.approve = True
                    borrower_request.approve_date = datetime.now()
                    borrower_request.save()
                    AdminEarning.objects.create(loan_id=borrower_request.id, pending_amount=borrower_request.amount)
                    emi_data1, emi_data, extra_days_interest, total_payable_amount =  emi_schedule(borrower_request.amount, borrower_request.fee, borrower_request.tenure, str(datetime.now().date()))
                    for i in emi_data1:
                        LoanEMISchedule.objects.create(loan_id=borrower_request.id, emi_amount=emi_data, 
                                                       emi_date=emi_data1[i]['emi_date'], user_id=borrower_request.user_id, 
                                                       received_amount=0, pending_amount=total_payable_amount)
                    return Response({
                        "status": True,
                        "message": f"Amount Transferred successfully to {borrower_request.user.name} wallet.",
                    })
                except DwollaError as e:
                    return Response(
                        {
                            'status':False,
                            'message': e.body['message']
                        },
                        e.status
                    )       
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class LoanCalculationAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            request_id = self.request.query_params.get("request_id")
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            if user_data.is_active and user_data.is_verified:
                if not request_id:
                    amount_request = BorrowerRequestAmount.objects.filter(lender_id=user_data.id).order_by('-id')
                    product_pagination = pagination.paginate_queryset(amount_request, request)
                    amount_serializer = LoanCalculationSerializer(product_pagination, many=True).data
                    pagination_record = pagination.get_paginated_response(amount_serializer).data
                    return Response({
                        "status": True,
                        "payload": pagination_record,
                        "message": "Loan calculation fetch.",
                    })
                else:
                    if BorrowerRequestAmount.objects.filter(lender_id=user_data.id, id=request_id).exists():
                        borrower_request = BorrowerRequestAmount.objects.get(id=request_id)
                        if borrower_request:
                            amount_serializer = BorrowerAmountRequestViewSerializer(borrower_request).data
                            return Response({
                                "status": True,
                                "payload": amount_serializer,
                                "message": "Request fetched.",
                            })
                        else:
                            return Response({
                                "status": True,
                                "message": "Invalid Request.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "No request found.",
                        })
            else:
                return Response({
                    "status": False,
                    "message": "Account not Active!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class EmiCalculator(APIView):
    parser_classes = [JSONParser]
    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            if not token:
                return Response(
                {
                    "status": False,
                    "message": "Please enter token.",
                },
                status=status.HTTP_401_UNAUTHORIZED
                )
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            data = request.data
            if data:
                if user_data.is_verified and user_data.is_active:
                    if (int(data['start_date'].split('-')[1]) <= 12 and int(data['start_date'].split('-')[1]) > 0) and (int(data['start_date'].split('-')[-1]) <= 31 and int(data['start_date'].split('-')[-1]) > 0) and (int(data['start_date'].split('-')[0]) > 0): 
                        serializer = EMICalculationSerializer(data=data, context={'user_id':user_data.id})
                        if serializer.is_valid():
                            if (datetime.strptime(data['start_date'], '%Y-%m-%d').date()) > date.today():
                                return Response({
                                    "status": True,
                                    'payload': serializer.data,
                                    "message": "EMI Calculation fetch.",
                                })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Date must be greater than current date.",
                                })   
                        else:
                            return Response({
                                "status": False,
                                "message": "Please Input validate field.",
                            })
                    else:
                        return Response({
                            "status": False,
                            "message": "Please Input valid date format.",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Account not active or email not verified yet.",
                    })
            else:
                return Response({
                    "status": False,
                    "message": "Please Input validate data!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class DaysOfEDI(APIView):
    def post(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            if user_data.is_active and user_data.is_verified:
                no_of_days = request.data.get('no_of_days')
                if not no_of_days:
                    return Response({
                        "status": False,
                        "message": "Please provide no of days.",
                    })
                
                edit_days_dict = get_days_for_edi(no_of_days)
                

            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })


class BidRequestAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            if not token:
                return Response(
                {
                    "status": False,
                    "message": "Please enter token.",
                },
                status=status.HTTP_401_UNAUTHORIZED
                )
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            data = request.data
            if not data:
                return Response({
                    "status": False,
                    "message": "Please Input validate data!",
                })
            if not user_data.is_verified and not user_data.is_active:
                return Response({
                    "status": False,
                    "message": "Account is not verified or active.",
                })
            serializer = BidRequestAcceptRejectSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data!",
                })
            bid_request = BidRequest.objects.filter(id=data['bid_id'])
            if not bid_request.exists():
                return Response({
                    "status": False,
                    "message": "Invalid bid request.",
                })
            
            if datetime.now() > (bid_request.first().created + timedelta(minutes=5)):
                BorrowerRequestAmount.objects.get(bid_id=data['bid_id'], lender_id=user_data.id).delete()
                return Response({
                    "status": False,
                    "message": "Your Biding is Expired",
                })

            time_limit_for_10 = datetime.strptime(str(datetime.now())[:19], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=10)
            if not BorrowerRequestAmount.objects.filter(bid_id=data['bid_id'], lender_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "No bid request found.",
                    })
            if data['request_type'] == 'accept':
                if Biding.objects.filter(bid_id=data['bid_id'], lender_id=user_data.id).exists():
                    return Response({
                        "status": False,
                        "message": "You already accepted the bid request.",
                    })
                borrower_request = BorrowerRequestAmount.objects.get(bid_id=data['bid_id'], lender_id=user_data.id)
                Biding.objects.create(bid_id=data['bid_id'], user_id=borrower_request.user_id, amount=borrower_request.amount, tenure=borrower_request.tenure,
                                      fee=borrower_request.fee, lender_id=user_data.id, time_limit=time_limit_for_10)
                return Response({
                    "status": True,
                    "message": "Request accepted. Now you can start binding.",
                })
            if data['request_type'] == 'reject':
                borrower_request = BorrowerRequestAmount.objects.get(bid_id=data['bid_id'], lender_id=user_data.id).delete()
                return Response({
                    "status": True,
                    "message": "Request rejected.",
                })
            else:
                return Response({
                    "status": False,
                    "message": "request_type must be accept or reject only.",
                })
        except BorrowerRequestAmount.DoesNotExist:
            return Response({
                "status": False,
                "message": "Bid Request Expired",
            })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class EmiCalculatorForWeb(APIView):
    throttle_classes = [UserRateThrottle]
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_data = User.objects.get(id = data.get('user_id'))
            data['start_date'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            if data:
                if user_data.is_verified and user_data.is_active:
                    serializer = EMICalculationSerializer(data=data, context={'user_id':user_data.id})
                    if serializer.is_valid():
                        return Response({
                            "status": True,
                            'payload': serializer.data,
                            "message": "EMI Calculation fetch.",
                        })
                    else:
                        return Response({
                            "status": False,
                            "message": "All Field is required",
                        })
                else:
                    return Response({
                        "status": False,
                        "message": "Account not active or email not verified yet.",
                    })
            else:
                return Response({
                    "status": False,
                    "message": "Please Input validate data!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class ContactLenderListAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            name = self.request.query_params.get('name')
            mobile = self.request.query_params.get('mobile')
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            queryset = Q()
            if name:
                queryset &= Q(name__contains=name)
            if mobile:
                queryset &= Q(mobile__contains=mobile)
            if user_data.is_active and user_data.is_verified:
                verified_user = LenderWallet.objects.all().values_list('user_id', flat=True)
                contact_list = ContactList.objects.filter(user_id=user_data.id).values_list('mobile_number')
                lender_list = User.objects.filter(mobile__in=contact_list, is_superuser=False, is_verified=True, is_active=True, mobile_verified=True).filter(queryset).filter(id__in=verified_user).exclude(id=user_data.id)
                lender_pagination = pagination.paginate_queryset(lender_list, request)
                serializer = UserViewSerializer(lender_pagination, many=True).data
                pagination_record = pagination.get_paginated_response(serializer).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "Contact Lender fetched.",
                })
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class BorrowerLoanLimitAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            if user_data.is_active and user_data.is_verified:
                loan_limit = LoanManagement.objects.all().first()
                loan_data = dict(
                    min_amount=100,
                    max_amount=int(loan_limit.amount),
                    min_fee=1,
                    max_fee=int(loan_limit.interest),
                    min_tenure=1,
                    max_tenure=loan_limit.tenure_month
                )
                return Response({
                    "status": True,
                    "payload": loan_data,
                    "message": "Loan Condition fetched.",
                })
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })
   
class LenderBiding(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            if user_data.is_active and user_data.is_verified:
                bid_id = request.query_params.get('bid_id')
                data = Biding.objects.filter(bid_id=bid_id).order_by("created")
                print(data.values('lender__email', 'created'), "-=-=-=-=-=")
                borrower = data.first().user
                serializer = LenderBidingDataSerializer(data, many=True).data
                user_serializer = UserInformationSerializer(borrower).data
                borrower_request_data = BorrowerRequestAmount.objects.filter(bid_id=bid_id).values('amount', 'tenure', 'fee').first()
                borrower_req_data = {
                    "amount": float(borrower_request_data.get("amount")),
                    "tenure": borrower_request_data.get("tenure"),
                    "fee": float(borrower_request_data.get("fee"))
                }
                borrower_data = dict(**user_serializer, **borrower_req_data)
                return Response({
                    "status": True,
                    "payload": {'borrower': borrower_data, 'lenders':serializer},
                    "message": "Lender Biding Data Fetched",
                })
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                })
        except:
            return Response({
                "status": False,
                "message": "something went wrong",
            })

    def patch(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            if user_data.is_active and user_data.is_verified:
                req_data = request.data
                if not req_data.get('bid_id') and not not req_data.get('fee'):
                    return Response({
                        "status": False,
                        "message": "All Field is required",
                    })
                bid_request_id = req_data['bid_id']
                biding_obj = Biding.objects.get(bid_id=bid_request_id, lender_id=user_data.id)
                current_time = datetime.now()
                data = {
                    'fee': req_data['fee'],
                    'time_limit': current_time + timedelta(minutes=5),
                }
                serializer = LenderBidingSerializer(instance=biding_obj, data=data)
                if serializer.is_valid():
                    test = serializer.save()
                    test.created = current_time
                    test.save()
                    return Response({
                        "status": True,
                        "message": "Biding request.",
                    })
                else:
                    return Response({
                        "status": False,
                        "message": "All Field is required",
                    })
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })
        
class BidRequestList(APIView):
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            if user_data.is_active and user_data.is_verified:
                user_type = request.query_params.get('user_type')
                pagination = PageNumberPagination()
                pagination.page_size = GLOBAL_PAGINATION_RECORD
                pagination.page_size_query_param = "page_size"
                
                
                if user_type == "BORROWER":
                    data_for_serializer = BidRequest.objects.filter(borrower_id=user_data.id)
                    pagination_data = BidRequestListForBorrowerSerializer(data_for_serializer, many=True).data
                elif user_type == "LENDER":
                    data_for_serializer = BorrowerRequestAmount.objects.filter(lender_id=user_data.id)
                    serializer = BidRequestListForLenderSerializer(data_for_serializer, many=True).data
                    pagination_data = []
                    for i in serializer:
                        for j in i:
                            if j == 'bid':
                                pagination_data.append(i[j])
                else:
                    return Response({
                        "status": False,
                        "message": "Please provide a valid user_type",
                    })
                pagination.paginate_queryset(data_for_serializer, request)
                pagination_record = pagination.get_paginated_response(pagination_data).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "Borrower Biding Data Fetched",
                })
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })

class BidingRequestLockProcedure(APIView):
    def post(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            if user_data.is_active and user_data.is_verified:
                user_type = request.data.get('user_type')
                bid_id = request.data.get('bid_id')
                if not user_type or not bid_id:
                    return Response({
                        "status": False,
                        "message": "user_type and bid_id is required",
                    })
                
                if user_type == "BORROWER":
                    biding = Biding.objects.get(bid_id=bid_id, user_id=user_data.id)
                    biding.user_lock = True
                    biding.save()
                    return Response({
                        "status": True,
                        "message": "Bid offer locked by borrower",
                    })
                elif user_type == "LENDER":
                    biding = Biding.objects.get(bid_id=bid_id, lender_id=user_data.id)
                    biding.lender_lock = True
                    biding.save()
                    return Response({
                        "status": True,
                        "message": "Bid offer locked by lender",
                    })
                else:
                    return Response({
                        "status": False,
                        "message": "Please provide a valid user_type",
                    })
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                })
        except Biding.DoesNotExist:
            return Response({
                "status": False,
                "message": "Bid not found",
            })
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            })