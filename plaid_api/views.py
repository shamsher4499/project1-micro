import json
from rest_framework.response import Response
from rest_framework.views import APIView
from superadmin.models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from .utils import ItemToken, ExchangeToken, ProcessorToken
from api.dwolla_payment import DwollaPlaidAPI
from api.status_code import *
from api.jwt import *
from dwollav2.error import Error as DwollaError

# Create your views here.
class PlaidItemTokenAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                if not user_data.is_active and not user_data.is_verified:
                    return Response({
                        "status": False,
                        "message": "Unauthenticated user!",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
                dwolla_user = DwollaCustomer.objects.all()
                if not dwolla_user.filter(user_id=user_data.id).exists():
                    return Response({
                        "status": False,
                        "message": "Dwolla Account not found!",
                    },
                    HTTP_404_NOT_FOUND
                    )
                link_token = ItemToken.create_link_token()
                return Response({
                    'status':True,
                    'payload':eval(link_token)['link_token'],
                    'message':'Item token generated.'
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
                'status':False,
                'message':'Something went wrong!'
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class FundingSourceAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            if request.META['HTTP_ACCEPT'].split(';')[0] == 'application/json' or request.META['CONTENT_TYPE'].split(';')[0] == 'application/json':
                data1 = authenticate(request)
                user_data = User.objects.get(id = data1['user_id'])
                if not user_data.is_active and not user_data.is_verified:
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
                serializer = FundingSourceSerializer(data=data)
                if not serializer.is_valid():
                    return Response({
                        "status": False,
                        "message": "Please Input validate data!.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
                dwolla_user = DwollaCustomer.objects.all()
                if not dwolla_user.filter(user_id=user_data.id).exists():
                    return Response({
                        "status": False,
                        "message": "Dwolla Account not found!",
                    },
                    HTTP_404_NOT_FOUND
                    )
                try:
                    dwolla_customer = dwolla_user.get(user_id=user_data.id)
                    exchange_token = ExchangeToken.exchange_token(data['public_token'])
                    if exchange_token == 400:
                            return Response(
                        {
                            'status':False,
                            'message': 'Server not responding.'
                        },
                        HTTP_400_BAD_REQUEST
                        )
                    processor_token = ProcessorToken.processor_token(exchange_token['access_token'], data['account_id'])
                    if processor_token == 400:
                            return Response(
                        {
                            'status':False,
                            'message': 'Server not responding.'
                        },
                        HTTP_400_BAD_REQUEST
                        )
                    customer_data = {
                        'customer_id':dwolla_customer.dwolla_id,
                        'name':data['bank_name'],
                    }
                    dwolla_plaid_token = DwollaPlaidAPI.create_plaid_token(customer_data, processor_token['processor_token'])
                    DwollaBankAccount.objects.create(user_id=user_data.id, dwolla_id=dwolla_customer.id, funding_source_id=dwolla_plaid_token)
                    return Response(
                    {
                        'status':True,
                        'message': 'Bank account added.'
                    },
                    HTTP_201_CREATED
                    )
                except DwollaError as e:
                    return Response(
                        {
                            'status':False,
                            'message': e.body['message'].split(':')[0]
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
                'status':False,
                'message':'Something went wrong!'
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

class FundingSourceAPIForWeb(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        # try:
            data = json.loads(request.body.decode('utf-8'))
            user_data = User.objects.get(slug = data.get('user_slug'))
            if not user_data.is_active and not user_data.is_verified:
                return Response({
                    "status": False,
                    "message": "Unauthenticated user!",
                },
                HTTP_401_UNAUTHORIZED
                )
            
            if not data:
                return Response({
                    "status": False,
                    "message": "Please Input validate data!.",
                },
                HTTP_400_BAD_REQUEST
                )
            serializer = FundingSourceSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data!.",
                },
                HTTP_400_BAD_REQUEST
                )
            dwolla_user = DwollaCustomer.objects.all()
            if not dwolla_user.filter(user_id=user_data.id).exists():
                return Response({
                    "status": False,
                    "message": "Dwolla Account not found!",
                },
                HTTP_404_NOT_FOUND
                )
            try:
                dwolla_customer = dwolla_user.get(user_id=user_data.id)
                exchange_token = ExchangeToken.exchange_token(data['public_token'])
                if exchange_token == 400:
                        return Response(
                    {
                        'status':False,
                        'message': 'Server not responding.'
                    },
                    HTTP_400_BAD_REQUEST
                    )
                processor_token = ProcessorToken.processor_token(exchange_token['access_token'], data['account_id'])
                if processor_token == 400:
                        return Response(
                    {
                        'status':False,
                        'message': 'Server not responding.'
                    },
                    HTTP_400_BAD_REQUEST
                    )
                customer_data = {
                    'customer_id':dwolla_customer.dwolla_id,
                    'name':data['bank_name'],
                }
                dwolla_plaid_token = DwollaPlaidAPI.create_plaid_token(customer_data, processor_token['processor_token'])
                DwollaBankAccount.objects.create(user_id=user_data.id, dwolla_id=dwolla_customer.id, funding_source_id=dwolla_plaid_token)
                return Response(
                {
                    'status':True,
                    'message': 'Bank account added.'
                },
                HTTP_201_CREATED
                )
            except DwollaError as e:
                return Response(
                    {
                        'status':False,
                        'message': e.body['message'].split(':')[0]
                    },
                    e.status
                )
    
        # except:
        #     return Response({
        #         'status':False,
        #         'message':'Something went wrong!'
        #     },
        #     HTTP_500_INTERNAL_SERVER_ERROR
        #     )