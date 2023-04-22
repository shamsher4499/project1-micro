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
from api.status_code import *
from api.dwolla_payment import check_wallet_amount, DwollaTransferAPI
from dwollav2.error import Error as DwollaError


class CardTokenAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            record_no = self.request.query_params.get("record_no")
            if user_data.is_active and user_data.is_verified:
                customer = stripe.Customer.retrieve(user_data.customer_id)
                cards = stripe.Customer.list_sources(
                        user_data.customer_id,
                        object="card",
                        limit=int(record_no if record_no else 100),
                    )
                return Response({
                    "status": True,
                    "payload": cards,
                    'default_card':customer.default_source,
                    "message": "Card fetched.",
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
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = CardTokenSerializer(data=data)
                    if serializer.is_valid():
                        try:
                            user_token = stripe.Customer.create_source(
                                user_data.customer_id,
                                source=data['card_token']
                                )
                            CardToken.objects.create(user_id=user_data.id, token=data['card_token'], card_id=user_token['id'])
                            stripe.Customer.modify_source(
                                user_data.customer_id,
                                user_token['id'],
                                name=data['card_holder_name'],
                                )
                            return Response({
                                "status": True,
                                "message": "Card added.",
                            })
                        except TypeError as e:
                            return Response({
                                "status": False,
                                "message": e,
                            })
                        except ValueError as e:
                            return Response({
                                "status": False,
                                "message": e,
                            })
                        except stripe.error.CardError as e:
                            return Response({
                                "status": False,
                                "message": e.user_message,
                            })
                        except Exception as e:
                            return Response({
                                "status": False,
                                "message": e.user_message,
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

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def put(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
                data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = CardTokenUpdateSerializer(data=data)
                    if serializer.is_valid():
                        if not CardToken.objects.filter(user_id=user_data.id, card_id=data['card_id']).exists():
                            return Response({
                                "status": False,
                                "message": "Card not found!",
                            })
                        try:
                            stripe.Customer.modify_source(
                                user_data.customer_id,
                                data['card_id'],
                                name=data['card_holder_name'],
                                )
                            return Response({
                                "status": True,
                                "message": "Card updated.",
                            })
                        except TypeError as e:
                            return Response({
                                "status": False,
                                "message": e,
                            })
                        except ValueError as e:
                            return Response({
                                "status": False,
                                "message": e,
                            })
                        except stripe.error.CardError as e:
                            return Response({
                                "status": False,
                                "message": e.user_message,
                            })
                        except Exception as e:
                            return Response({
                                "status": False,
                                "message": e.user_message,
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

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            data1 = jwt.decode(token, 'secret', algorithms=['HS256'], options=jwt_options)
            user_data = User.objects.get(id = data1['user_id'])
            card_id = self.request.query_params.get("card_id")
            if user_data.is_active and user_data.is_verified:
                user_cards = CardToken.objects.filter(card_id=card_id, user_id=user_data.id)
                if user_cards.exists():
                    user_cards.delete()
                    stripe.Customer.delete_source(
                            request.user.customer_id,
                            card_id,
                    )
                    return Response({
                        "status": True,
                        "message": "Card deleted.",
                    })
                else:
                    return Response({
                        "status": False,
                        "message": "Card not found!",
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

class UserPlanAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            if user_data.is_active and user_data.is_verified:
                plan = SubscriptionPlan.objects.filter(name='Premium Plan')
                serializer = SubscriptionPlanSerializer(plan, many=True, context={'user':user_data.id}).data
                return Response({
                    "status": True,
                    "payload": serializer,
                    "message": "Subscription plans fetched.",
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
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = SubscriptionCheckoutSerializer(data=data)
                    if serializer.is_valid():
                        subscription_plans = SubscriptionPlan.objects.all()
                        if not subscription_plans.filter(id=data['plan_id']).exists():
                            return Response({
                                "status": False,
                                "message": "Plan not found!",
                            })
                        if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                            return Response({
                                "status": False,
                                "message": "Wallet not found!",
                            })
                        if UserSubscription.objects.filter(user_id=user_data.id).exists():
                            return Response({
                                "status": False,
                                "message": "You have already subscribed!",
                            })
                        dwolla_wallet = LenderWallet.objects.get(user_id=user_data.id)
                        admin_wallet = AdminAccount.objects.all()
                        subscription_price = SubscriptionPlan.objects.get(id=data['plan_id'])
                        if not check_wallet_amount(wallet_id=dwolla_wallet.wallet_id, amount=subscription_price.original_price):
                            return Response({
                                "status": False,
                                "message": "You have insufficient balance in your wallet."
                            })
                        try:
                            transfer_data = {
                                'amount': f'{subscription_price.original_price}',
                                'funding_source': f'{dwolla_wallet.wallet_id}',
                                'destination_source': f'{admin_wallet.first().wallet_id}',
                                'message': f"Subscription plan purchase by {user_data.name}"
                            }
                            DwollaTransferAPI.create_transfer(transfer_data)
                            plan_start_date = datetime.now().date() 
                            plan_end_date = datetime.now().date() + timedelta(days=30)
                            UserSubscription.objects.create(user_id=user_data.id, subscription_id=subscription_price.id, 
                            amount=subscription_plans.get(id=data['plan_id']).original_price, status='ACTIVE', 
                            plan=subscription_plans.get(id=data['plan_id']).name, current_period_end=plan_end_date, 
                            current_period_start=plan_start_date)
                            return Response({
                                "status": True,
                                "message": "Subscription started successfully.",
                            })
                        except TypeError as e:
                            return Response({
                                "status": False,
                                "message": e,
                            })
                        except ValueError as e:
                            return Response({
                                "status": False,
                                "message": e,
                            })
                        except Exception as e:
                            return Response({
                                "status": False,
                                "message": ' '.join(e),
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

class DefaultCardAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = DefaultCardSerializer(data=data)
                    if serializer.is_valid():
                        user_cards = CardToken.objects.filter(user_id=user_data.id)
                        if user_cards.filter(card_id=data['card_id']).exists():
                            try:
                                customer = stripe.Customer.retrieve(user_data.customer_id)
                                customer.default_source = data['card_id']
                                customer.save()
                                return Response({
                                    "status": True,
                                    "message": "Card updated.",
                                })
                            except TypeError as e:
                                return Response({
                                    "status": False,
                                    "message": e,
                                })
                            except ValueError as e:
                                return Response({
                                    "status": False,
                                    "message": e,
                                })
                            except stripe.error.CardError as e:
                                return Response({
                                    "status": False,
                                    "message": e.user_message,
                                })
                            except Exception as e:
                                return Response({
                                    "status": False,
                                    "message": e.user_message,
                                    })
                        else:
                            return Response({
                                "status": False,
                                "message": "No Card found!",
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

class StorePlanAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            if user_data.is_active and user_data.is_verified:
                plan = StoreSubscriptionPlan.objects.all().order_by('-id')
                serializer = StoreSubscriptionPlanSerializer(plan, many=True, context={'user':user_data.id}).data
                return Response({
                    "status": True,
                    "payload": serializer,
                    "message": "Subscription plans fetched.",
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
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                data = request.data
                if data:
                    serializer = SubscriptionCheckoutSerializer(data=data)
                    if serializer.is_valid():
                        if not user_data.is_store:
                            return Response({
                                "status": False,
                                "message": "User must be logged in as a Store.",
                            })
                        subscription_plans = StoreSubscriptionPlan.objects.all()
                        if not subscription_plans.filter(id=data['plan_id']).exists():
                            return Response({
                                "status": False,
                                "message": "Plan not found!",
                            })
                        if StoreSubscription.objects.filter(user_id=user_data.id).exists():
                            return Response({
                                "status": False,
                                "message": "You have already subscribed!",
                            })
                        if not LenderWallet.objects.filter(user_id=user_data.id).exists():
                            return Response({
                                "status": False,
                                "message": "Bank account not found."
                            })
                        dwolla_wallet = LenderWallet.objects.get(user_id=user_data.id)
                        subscription_price = StoreSubscriptionPlan.objects.get(id=data['plan_id'])
                        admin_wallet = AdminAccount.objects.all()
                        if not check_wallet_amount(wallet_id=dwolla_wallet.wallet_id, amount=subscription_price.price):
                            return Response({
                                "status": False,
                                "message": "You have insufficient balance in your wallet."
                            })
                        with transaction.atomic():
                            try:
                                transfer_data = {
                                    'amount': f'{subscription_price.price}',
                                    'funding_source': f'{dwolla_wallet.wallet_id}',
                                    'destination_source': f'{admin_wallet.first().wallet_id}',
                                    'message': f"Subscription plan purchase by {user_data.name}"
                                }
                                DwollaTransferAPI.create_transfer(transfer_data)
                                plan_start_date = datetime.now().date() 
                                plan_end_date = datetime.now().date() + timedelta(days=30)
                                StoreSubscription.objects.create(user_id=user_data.id, subscription_id=subscription_price.id, 
                                amount=subscription_plans.get(id=data['plan_id']).price, status='ACTIVE', 
                                plan=subscription_plans.get(id=data['plan_id']).name, current_period_end=plan_end_date, 
                                current_period_start=plan_start_date)
                                return Response({
                                    "status": True,
                                    "message": "Subscription started successfully.",
                                })
                            except DwollaError as e:
                                return Response(
                                    {
                                        'status':False,
                                        'message': e.body['message']
                                    },
                                    e.status
                                ) 
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
        
class TransferAmountIntoBankAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                if user_data.is_active and user_data.is_verified:
                    return Response({
                        "status": False,
                        "message": "Unauthenticated user!",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
                data = request.data
                if not data:
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                serializer = TransferAmountBankSerializer(data=data)
                if not serializer.is_valid():
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                if not DwollaBankAccount.objects.filter(user_id=user_data.id, funding_source_id=data['bank_id']).exists():
                    return Response({
                        "status": False,
                        "message": "Bank account not found!",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                lender_wallet = LenderWallet.objects.get(user_id=user_data.id)
                if not check_wallet_amount(wallet_id=lender_wallet.wallet_id, amount=data['amount']):
                    return Response({
                        "status": False,
                        "message": "You have insufficient balance in your wallet."
                    })
                with transaction.atomic():
                    try:
                        request_data = {
                            'id':lender_wallet.id,
                            'funding_source': lender_wallet.wallet_id,
                            'destination_source': data['bank_id'],
                            'amount': data['amount'],
                            'message': "Amount Transfer wallet to bank."
                        }
                        DwollaTransferAPI.create_transfer(request_data)
                        return Response({
                            'status': True,
                            'message': 'Amount Transfer successfully.'
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