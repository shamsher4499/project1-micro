from superadmin.models import *
from .serializers import *
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
import json

class ActiveLoanAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            user_data = User.objects.get(id = data1['user_id'])
            queryset = Q()
            if 2 < request.query_params.__len__():
                return Response({
                    "status": False,
                    "message": "Please search only valid parameter!",
                },
                HTTP_400_BAD_REQUEST
                )
            # if list(request.query_params.keys()) != ['user_type', 'page'] or list(request.query_params.keys()) != ['user_type']:
            #     return Response({
            #         "status": False,
            #         "message": "Please search only valid parameter!",
            #     },
            #     HTTP_400_BAD_REQUEST
            #     )
            user_type = request.query_params.get("user_type", None)
            if user_type == None:
                return Response({
                    "status": False,
                    "message": "Please select a user type!",
                },
                HTTP_400_BAD_REQUEST
                )
            if user_type not in ['LENDER', 'BORROWER', 'LENDING_BOX']:
                return Response({
                    "status": False,
                    "message": "Please select a valid user type!",
                },
                HTTP_400_BAD_REQUEST
                )
            if user_data.is_active and user_data.is_verified:
                if user_type == "LENDER":
                    queryset &= Q(lender_id=user_data.id)
                if user_type == 'BORROWER':
                    queryset &= Q(user_id=user_data.id)
                if user_type == 'LENDING_BOX':
                    queryset &= Q(store_id=user_data.id)
                if user_type != 'LENDING_BOX':
                    borrower_request = BorrowerRequestAmount.objects.filter(queryset, approve=1, completed=0).order_by('-id')
                    store_pagination = pagination.paginate_queryset(borrower_request, request)
                    borrower_request_serialized = ActiveLoanSerializer(store_pagination, many=True, context={'user':user_data.id, 'user_type':user_type}).data
                    pagination_record = pagination.get_paginated_response(borrower_request_serialized).data
                    return Response({
                        "status": True,
                        "payload": pagination_record,
                        "message": "Active loans fetched successfully.",
                    },
                    HTTP_200_OK
                    )
                store_loans = StoreLoanEmi.objects.filter(queryset, approve=1, completed=0).order_by('-id')
                store_pagination = pagination.paginate_queryset(store_loans, request)
                borrower_request_serialized = LendingBoxActiveLoanSerializer(store_pagination, many=True, context={'user':user_data.id, 'user_type':user_type}).data
                pagination_record = pagination.get_paginated_response(borrower_request_serialized).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "Active loans fetched successfully.",
                },
                HTTP_200_OK
                )
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                },
                HTTP_401_UNAUTHORIZED
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

class CompletedLoanAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            user_data = User.objects.get(id = data1['user_id'])
            user_type = request.query_params.get("user_type", None)
            queryset = Q()
            if user_type == None:
                return Response({
                    "status": False,
                    "message": "Please select a user type!",
                },
                HTTP_400_BAD_REQUEST
                )
            if user_type not in ['LENDER', 'BORROWER', 'LENDING_BOX']:
                return Response({
                    "status": False,
                    "message": "Please select a valid user type!",
                },
                HTTP_400_BAD_REQUEST
                )
            if user_data.is_active and user_data.is_verified:
                if user_type == "LENDER":
                    queryset &= Q(lender_id=user_data.id)
                if user_type == 'BORROWER':
                    queryset &= Q(user_id=user_data.id)
                if user_type == 'LENDING_BOX':
                    queryset &= Q(store_id=user_data.id)
                if user_type != 'LENDING_BOX':
                    borrower_request = BorrowerRequestAmount.objects.filter(queryset, approve=1, completed=1).order_by('-id')
                    store_pagination = pagination.paginate_queryset(borrower_request, request)
                    borrower_request_serialized = ActiveLoanSerializer(store_pagination, many=True, context={'user':user_data.id, 'user_type':user_type}).data
                    pagination_record = pagination.get_paginated_response(borrower_request_serialized).data
                    return Response({
                        "status": True,
                        "payload": pagination_record,
                        "message": "Completed loans fetched successfully.",
                    },
                    HTTP_200_OK
                    )
                store_loans = StoreLoanEmi.objects.filter(queryset, approve=1, completed=1).order_by('-id')
                store_pagination = pagination.paginate_queryset(store_loans, request)
                borrower_request_serialized = LendingBoxActiveLoanSerializer(store_pagination, many=True, context={'user':user_data.id, 'user_type':user_type}).data
                pagination_record = pagination.get_paginated_response(borrower_request_serialized).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "Completed loans fetched successfully.",
                },
                HTTP_200_OK
                )
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                },
                HTTP_401_UNAUTHORIZED
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

class TransferLoanUserAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            user_data = User.objects.get(id = data1['user_id'])
            loan_id = request.query_params.get("loan_id", None)
            if user_data.is_active and user_data.is_verified:
                all_loans = BorrowerRequestAmount.objects.all()
                if not all_loans.filter(user_id=user_data.id, id=loan_id, request_type='DIRECT').exists():
                    return Response({
                        "status": False,
                        "message": "No Loan found."
                    },
                    HTTP_400_BAD_REQUEST
                    )
                user_loan = BorrowerRequestAmount.objects.get(id=loan_id)
                remove_user = [user_loan.lender_id, user_data.id]
                all_users = User.objects.filter(is_superuser=False, is_active=True, is_verified=True,
                                                mobile_verified=True).values_list('mobile', flat=True).exclude(id__in=remove_user)
                contact_users = ContactList.objects.filter(user_id=user_data.id, mobile_number__in=all_users).order_by('-id')
                store_pagination = pagination.paginate_queryset(contact_users, request)
                borrower_request_serialized = TransferLoanUserSerializer(store_pagination, many=True).data
                pagination_record = pagination.get_paginated_response(borrower_request_serialized).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "Active loans fetched successfully.",
                },
                HTTP_200_OK
                )
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                },
                HTTP_401_UNAUTHORIZED
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )

class TransferLoanAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            user_data = User.objects.get(id = data1['user_id'])
            user_type = request.query_params.get("user_type", None)
            if user_data.is_active and user_data.is_verified:
                borrower_request = BorrowerRequestAmount.objects.filter(user_id=user_data.id, approve=1, completed=0).order_by('-id')
                store_pagination = pagination.paginate_queryset(borrower_request, request)
                borrower_request_serialized = ActiveLoanSerializer(store_pagination, many=True, context={'user':user_data.id, 'user_type':user_type}).data
                pagination_record = pagination.get_paginated_response(borrower_request_serialized).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "Active loans fetched successfully.",
                },
                HTTP_200_OK
                )
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                },
                HTTP_401_UNAUTHORIZED
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            data = request.data
            if not data:
                return Response({
                    "status": False,
                    "message": "Please input valid data.",
                },
                HTTP_400_BAD_REQUEST
                )
            serializers = TransferLoanRequestSerializer(data=data)
            if not serializers.is_valid():
                return Response({
                    "status": False,
                    "message": "Please input valid data.",
                },
                HTTP_400_BAD_REQUEST
                )
            if not user_data.is_active and not user_data.is_verified:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                },
                HTTP_401_UNAUTHORIZED
                )
            if TransferLoanRequest.objects.filter(user_id=user_data.id).exists():
                return Response({
                    "status": False,
                    "message": "You have already sent transfer request!",
                },
                HTTP_400_BAD_REQUEST
                )
            if not BorrowerRequestAmount.objects.filter(id=data['loan_id']):
                return Response({
                    "status": False,
                    "message": "Invalid Loan Request!",
                },
                HTTP_400_BAD_REQUEST
                )
            transfer_data = TransferLoanRequest.objects.create(user_id=user_data.id, loan_id=data['loan_id'])
            for i in json.loads(data['user_list']):
                if User.objects.filter(id=i).exists():
                   TransferLoanRequestUser.objects.create(transfer_id=transfer_data.id, transfer_user_id=i, loan_id=data['loan_id'])
            return Response({
                "status": True,
                "message": "Request sent successfully.",
            },
            HTTP_200_OK
            )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )
       
class TransferLoanRequestStatusAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            user_data = User.objects.get(id = data1['user_id'])
            loan_id = request.query_params.get("loan_id", None)
            if user_data.is_active and user_data.is_verified:
                if not loan_id:
                    transfer_request = TransferLoanRequest.objects.filter(user_id=user_data.id)
                    store_pagination = pagination.paginate_queryset(transfer_request, request)
                    borrower_request_serialized = TransferLoanRequestViewSerializer(store_pagination, many=True).data
                    pagination_record = pagination.get_paginated_response(borrower_request_serialized).data
                    return Response({
                        "status": True,
                        "payload": pagination_record,
                        "message": "Transfer request fetched successfully.",
                    },
                    HTTP_200_OK
                    )
                transfer_request = TransferLoanRequestUser.objects.filter(loan_id=loan_id)
                store_pagination = pagination.paginate_queryset(transfer_request, request)
                borrower_request_serialized = TransferLoanRequestStatusSerializer(store_pagination, many=True).data
                pagination_record = pagination.get_paginated_response(borrower_request_serialized).data
                return Response({
                    "status": True,
                    "payload": pagination_record,
                    "message": "Transfer request fetched successfully.",
                },
                HTTP_200_OK
                )
            else:
                return Response({
                    "status": False,
                    "message": "Unauthenticated User!",
                },
                HTTP_401_UNAUTHORIZED
                )
        except:
            return Response({
                "status": False,
                "message": "Something Went Wrong.",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class EmiScheduleAPI(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            data1 = authenticate(request)
            user_data = User.objects.get(id = data1['user_id'])
            loan_id = self.request.query_params.get("loan_id")
            pagination = PageNumberPagination()
            pagination.page_size = GLOBAL_PAGINATION_RECORD
            pagination.page_size_query_param = "page_size"
            if user_data.is_active and user_data.is_verified:
                if not loan_id:
                    return Response({
                    "status": False,
                    "message": "Please enter a valid loan ID.",
                },
                HTTP_400_BAD_REQUEST
                )
                loan_emi = LoanEMISchedule.objects.filter(loan_id=loan_id, user_id=user_data.id)
                loan_emi_serializer = EmiScheduleSerializer(loan_emi, many=True).data
                return Response({
                    "status": True,
                    "payload": loan_emi_serializer,
                    "message": "Loan Emi schedule fetched.",
                },
                HTTP_200_OK
                )
            else:
                return Response({
                    "status": False,
                    "message": "Account not Active!",
                },
                HTTP_401_UNAUTHORIZED
                )
        except:
            return Response({
                "status": False,
                "message": "Something went wrong!",
            },
            HTTP_500_INTERNAL_SERVER_ERROR
            )