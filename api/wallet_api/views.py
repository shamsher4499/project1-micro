from superadmin.models import *
from .serializers import *
from django.db import transaction, IntegrityError
from rest_framework.pagination import PageNumberPagination
from .email import *
from api.utils import *
from api.jwt import *
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
import jwt
from api.dwolla_payment import DwollaCheckBalanceAPI

class LenderAddAmountAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                if user_data.is_active and user_data.is_verified:
                    if not LenderWallet.objects.filter(user_id=user_data.id).exists():
                        return Response({
                            "status": True,
                            'wallet_setup': False,
                            'payload': f'$0',
                            "message": "Wallet amount.",
                        })
                    wallet = LenderWallet.objects.get(user_id=user_data.id)
                    customer_amount = DwollaCheckBalanceAPI.get_balance(wallet.wallet_id)
                    return Response({
                    "status": True,
                    'wallet_setup': True,
                    'payload': customer_amount,
                    "message": "Wallet Amount.",
                    })
                else:
                    return Response({
                        "status": False,
                        "message": "Unauthenticated User!",
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
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                admin_wallet_limit = WalletAmountLimit.objects.get(id=1)
                if data:
                    serializer = LenderAddAmountSerializer(data=data)
                    if serializer.is_valid():
                        if user_data.is_active and user_data.is_verified:
                            user_wallet_status = check_wallet_status(user_data.id)
                            if float(data['amount']):
                                try:
                                    with transaction.atomic():
                                        if not LenderWallet.objects.filter(user_id=user_data.id).exists(): 
                                            if float(data['amount']) < float(admin_wallet_limit.amount): #import from the utils
                                                lender_wallet = LenderWallet.objects.create(user_id=user_data.id, amount=data['amount'])
                                                LenderWalletTransaction.objects.create(amount=data['amount'], wallet_id=lender_wallet.id, status='CREDIT')
                                                return Response({
                                                    "status": True,
                                                    'message': f"${data['amount']} successfully added."
                                                })
                                            else:
                                                return Response({
                                                    "status": False,
                                                    'message': f'Amount must be less than ${int(admin_wallet_limit.amount)}.'
                                                })
                                        else:
                                            if user_wallet_status.get('status'):
                                                if float(data['amount']) < float(admin_wallet_limit.amount): #import from the utils
                                                    lender_wallet = LenderWallet.objects.get(user_id=user_data.id)
                                                    lender_wallet.amount = float(lender_wallet.amount) + float(data['amount'])
                                                    lender_wallet.save()
                                                    LenderWalletTransaction.objects.create(amount=data['amount'], wallet_id=lender_wallet.id, status='CREDIT')
                                                    return Response({
                                                        "status": True,
                                                        'message': f"${data['amount']} successfully added."
                                                    })
                                                else:
                                                    return Response({
                                                        "status": False,
                                                        'message': f'Amount must be less than ${int(admin_wallet_limit.amount)}.'
                                                    })
                                            else:
                                                return Response(user_wallet_status)
                                except:
                                    return Response({
                                    "status": False,
                                    'message': 'Something went wrong! Please try again later.'
                                })
                            else:
                                return Response({
                                    "status": False,
                                    "message": "Amount must be integer field only.",
                                })     
                        else:
                            return Response({
                                "status": False,
                                "message": "Account not verified or inactive!",
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

class LenderWalletTransactionAPI(APIView):
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
                user_wallet = LenderWallet.objects.filter(user_id=user_data.id)
                if user_data.is_active and user_data.is_verified:
                    if user_wallet.exists():
                        wallet = user_wallet.first()
                        wallet_transaction = LenderWalletTransaction.objects.filter(wallet_id=wallet.id).order_by('-id')
                        transaction_pagination = pagination.paginate_queryset(wallet_transaction, request)
                        serializer = LenderWalletTransactionSerializer(transaction_pagination, many=True).data
                        pagination_record = pagination.get_paginated_response(serializer).data
                        return Response({
                            "status": True,
                            "payload": pagination_record,
                            "message": "Wallet Transactions fetched.",
                        })
                    return Response({
                        "status": False,
                        "message": "No Transactions found!",
                    })
                else:
                    return Response({
                        "status": False,
                        "message": "Unauthenticated User!",
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