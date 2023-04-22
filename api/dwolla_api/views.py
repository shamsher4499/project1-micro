from superadmin.models import *
from .serializers import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import re
from api.fake_email import *
from .email import *
from api.utils import *
from api.jwt import *
from api.dwolla_payment import DwollaCustomerAPI, DwollaFundingSourceAPI, DwollaTransferAPI, DwollaCheckBalanceAPI, DwollaVerifyAPI, DwollaTransactionStatusAPI, DwollaTransactionHistoryAPI
from api.status_code import *
from dwollav2.error import Error as DwollaError
from api.dwolla_error import dwolla_error_code1


def check_password(password):
    return bool(re.match('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).{8,16}$', password))==True

class CustomerAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            dwolla_user = DwollaCustomer.objects.all()
            if not dwolla_user.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found!",
                    },
                    HTTP_400_BAD_REQUEST
                )
            try:
                dwolla = dwolla_user.get(user_id=user_data.id)
                dwolla_customer = DwollaCustomerAPI.get_customer(dwolla.dwolla_id)
                dwolla_bank = DwollaBankAccount.objects.filter(user_id=user_data.id).exists()
                return Response(
                    {
                        'status':True,
                        'bank_status':dwolla_bank,
                        'payload': dwolla_customer,
                        'message':'Customer profile fetched.'
                    },
                    HTTP_200_OK
                    )
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
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            if DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Your account is already created.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            data = request.data
            if user_data.is_verified == False:
                return Response({
                        "status": False,
                        "message": "Please check email, your email is not verified yet.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if user_data.is_active == False:
                return Response({
                        "status": False,
                        "message": "Your Account is Inactive. Please contact the Admin.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            serializer = DwollaCustomerSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data...",
                },
                HTTP_400_BAD_REQUEST
                )
            customer_data = {
                'firstName': data['firstName'],
                'lastName': data['lastName'],
                'email': data['email'],
                'type': data['type'],
                'address1':data['address1'],
                'city': data['city'],
                'state': data['state'],
                'postalCode':data['postalCode'],
                'dateOfBirth':data['dateOfBirth'],
                'ssn':data['ssn']
            }
            try:
                dwolla_customer = DwollaCustomerAPI.create_customer(customer_data)
                dwolla_wallet = DwollaFundingSourceAPI.get_wallet(dwolla_customer)
                DwollaCustomer.objects.create(user_id=user_data.id, dwolla_id=dwolla_customer)
                LenderWallet.objects.create(user_id=user_data.id, wallet_id=dwolla_wallet)
                return Response(
                    {
                        'status':True,
                        'message': 'Account created successfully.'
                    },
                    HTTP_201_CREATED
                    )
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
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def put(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found!",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            if user_data.is_verified == False:
                return Response({
                        "status": False,
                        "message": "Please check email, your email is not verified yet.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if user_data.is_active == False:
                return Response({
                        "status": False,
                        "message": "Your Account is Inactive. Please contact the Admin.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            data = request.data
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            serializer = DwollaCustomerSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data...",
                },
                HTTP_400_BAD_REQUEST
                )
            dwolla_customer = DwollaCustomer.objects.get(user_id=user_data.id)
            customer_data = {
                'firstName': data['firstName'],
                'lastName': data['lastName'],
                'email': data['email'],
                'type': data['type'],
                'businessName': data['businessName'],
                'customer_id':dwolla_customer.dwolla_id,
                'address1':data['address1'],
                'address2':data['address2'],
                'city': data['city'],
                'state': data['state'],
                'postalCode':data['postalCode'],
                'dateOfBirth':data['dateOfBirth'],
                'ssn':data['ssn']
            }
            try:
                dwolla_customer = DwollaCustomerAPI.update_customer(customer_data)
                return Response(
                    {
                        'status':True,
                        'message': 'Profile updated successfully.'
                    },
                    HTTP_200_OK
                    )
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
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

class FundingAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            dwolla_user = DwollaCustomer.objects.all()
            if not dwolla_user.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found!",
                    },
                    HTTP_400_BAD_REQUEST
                )
            try:
                dwolla = dwolla_user.get(user_id=user_data.id)
                dwolla_customer = DwollaFundingSourceAPI.get_all_funding(dwolla.dwolla_id)
                return Response(
                    {
                        'status':True,
                        'payload': dwolla_customer,
                        'message':'Funding Sources fetched.'
                    },
                    HTTP_200_OK
                    )
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
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            if user_data.is_verified == False:
                return Response({
                        "status": False,
                        "message": "Please check email, your email is not verified yet.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if user_data.is_active == False:
                return Response({
                        "status": False,
                        "message": "Your Account is Inactive. Please contact the Admin.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            data = request.data
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            serializer = FundingSourceSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data...",
                },
                HTTP_400_BAD_REQUEST
                )
            dwolla_user = DwollaCustomer.objects.get(user_id=user_data.id)
            funding_data = {
                'routingNumber': data['routingNumber'],
                'accountNumber': data['accountNumber'],
                'bankAccountType': data['bankAccountType'],
                'name': data['name'],
                'dwolla_id':dwolla_user.dwolla_id
            }
            try:
                dwolla_customer = DwollaFundingSourceAPI.create_funding(funding_data)
                DwollaBankAccount.objects.create(user_id=user_data.id, dwolla_id=dwolla_user.id, funding_source_id=dwolla_customer)
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
                        'message': e.body['message']
                    },
                    e.status
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
    def delete(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            funding_id = request.query_params.get("funding_id")
            if not funding_id:
                return Response({
                        "status": False,
                        "message": "Please enter valid funding id.",
                    },
                    HTTP_400_BAD_REQUEST
                )
            dwolla_user = DwollaCustomer.objects.all()
            if not dwolla_user.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found!",
                    },
                    HTTP_400_BAD_REQUEST
                )
            try:
                user_banks = DwollaBankAccount.objects.all()
                if not user_banks.filter(user_id = user_data.id, funding_source_id=funding_id).exists():
                    return Response({
                        "status": False,
                        "message": "Account not found!",
                    },
                    HTTP_400_BAD_REQUEST
                )
                DwollaFundingSourceAPI.remove_funding(funding_id)
                user_banks.filter(funding_source_id=funding_id).delete()
                return Response(
                    {
                        'status':True,
                        'message':'Bank Account removed!'
                    },
                    HTTP_200_OK
                    )
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
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

class TransferAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            if user_data.is_verified == False:
                return Response({
                        "status": False,
                        "message": "Please check email, your email is not verified yet.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if user_data.is_active == False:
                return Response({
                        "status": False,
                        "message": "Your Account is Inactive. Please contact the Admin.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            data = request.data
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            serializer = TransferSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data...",
                },
                HTTP_400_BAD_REQUEST
                )
            wallet_limit = WalletAmountLimit.objects.all()
            if float(data['amount']) > wallet_limit.first().amount:
                return Response({
                    "status": False,
                    "message": f"You can add only max ${wallet_limit.first().amount} amount.",
                },
                HTTP_400_BAD_REQUEST
                )
            user_wallet = LenderWallet.objects.get(user_id=user_data.id)
            transfer_data = {
                'amount': data['amount'],
                'funding_source': data['funding_source'],
                'destination_source': user_wallet.wallet_id,
                # 'destination_source': '4bc19f95-7a4e-40d3-be1d-f6ce346af2b4',
                'message':"Transfer amount"
            }
            try:
                DwollaTransferAPI.create_transfer(transfer_data)
                return Response(
                    {
                        'status':True,
                        'message': 'Amount transfer successfully.'
                    },
                    HTTP_201_CREATED
                    )
            except DwollaError as e:
                return Response(
                    {
                        'status':False,
                        'message': e.body['_embedded']['errors'][0]['message'] if e.body['_embedded']['errors'][0]['code'] else e.body['message']
                    },
                    e.status
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

class CheckBalanceAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            if user_data.is_verified == False:
                return Response({
                        "status": False,
                        "message": "Please check email, your email is not verified yet.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if user_data.is_active == False:
                return Response({
                        "status": False,
                        "message": "Your Account is Inactive. Please contact the Admin.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            data = request.data
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            serializer = CheckBalanceSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data...",
                },
                HTTP_400_BAD_REQUEST
                )
            try:
                customer_balance = DwollaCheckBalanceAPI.get_balance(data['source_id'])
                return Response(
                    {
                        'status':True,
                        'payload':customer_balance,
                        'message': 'Balance fetched!'
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
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )
          
class TransactionsHistoryAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            dwolla_user = DwollaCustomer.objects.all()
            if not dwolla_user.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Transaction not found!",
                    },
                    HTTP_400_BAD_REQUEST
                )
            try:
                dwolla = dwolla_user.get(user_id=user_data.id)
                customer_transactions = DwollaTransactionHistoryAPI.all_transactions(dwolla.dwolla_id)
                return Response(
                    {
                        'status':True,
                        'payload': customer_transactions,
                        'message':'All Transactions fetched!'
                    },
                    HTTP_200_OK
                    )
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
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            if user_data.is_verified == False:
                return Response({
                        "status": False,
                        "message": "Please check email, your email is not verified yet.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if user_data.is_active == False:
                return Response({
                        "status": False,
                        "message": "Your Account is Inactive. Please contact the Admin.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            data = request.data
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            serializer = TransactionStatusSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data...",
                },
                HTTP_400_BAD_REQUEST
                )
            try:
                transaction_status = DwollaTransactionStatusAPI.transaction_status(data['transaction_id'])
                return Response(
                    {
                        'status':True,
                        'message': 'status: ' + transaction_status
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
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class VerifyFundingSourceAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            if user_data.is_verified == False:
                return Response({
                        "status": False,
                        "message": "Please check email, your email is not verified yet.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if user_data.is_active == False:
                return Response({
                        "status": False,
                        "message": "Your Account is Inactive. Please contact the Admin.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            data = request.data
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            serializer = VerifyFundingSourceSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data...",
                },
                HTTP_400_BAD_REQUEST
                )
            try:
                DwollaVerifyAPI.verify_status(data['funding_id'])
                return Response(
                    {
                        'status':True,
                        'message': 'Account Verification Success.'
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
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class VerifyAmountAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
                return Response({
                        "status": False,
                        "message": "Account not found.",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            if user_data.is_verified == False:
                return Response({
                        "status": False,
                        "message": "Please check email, your email is not verified yet.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            if user_data.is_active == False:
                return Response({
                        "status": False,
                        "message": "Your Account is Inactive. Please contact the Admin.",
                    },
                    HTTP_401_UNAUTHORIZED
                    )
            data = request.data
            if not data:
                return Response({
                        "status": False,
                        "message": "Please Input validate data...",
                    },
                    HTTP_400_BAD_REQUEST
                    )
            serializer = VerifyAmountSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    "status": False,
                    "message": "Please Input validate data...",
                },
                HTTP_400_BAD_REQUEST
                )
            try:
                DwollaVerifyAPI.verify_amount(data)
                return Response(
                    {
                        'status':True,
                        'message': 'Micro-deposits successfully verified.'
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
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )