from api.auth_api.serializers import UserInformationSerializer
from superadmin.models import *
from rest_framework import serializers
from api.utils import loan_calculator
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from api.utils import numberOfDays, calculate_extra_days_interest
from numerize.numerize import numerize

class BorrowerAmountRequestSerializer(serializers.Serializer):
    request_type = serializers.CharField()
    amount = serializers.IntegerField()
    tenure = serializers.IntegerField()
    fee = serializers.CharField()

class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'calling_code', 'country_code', 'mobile', 'profile_pic']

class BorrowerAmountRequestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowerRequestAmount
        fields = ['id', 'request_type', 'amount', 'fee', 'tenure', 'approve', 'reject', 'lender', 'created']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['lender'] = UserViewSerializer(instance.lender).data
        return rep

class BorrowerAmountRequestViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowerRequestAmount
        fields = '__all__'

class LenderSendAmountSerializer(serializers.Serializer):
    request_id = serializers.CharField()
    approve_type = serializers.CharField()

class LenderViewRequestSerializer(serializers.ModelSerializer):
    loan_calculation = serializers.SerializerMethodField()
    class Meta:
        model = BorrowerRequestAmount
        fields = ['id', 'bid_id', 'request_type', 'amount', 'fee', 'loan_calculation', 'tenure', 'approve', 'user', 'created']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['user'] = UserViewSerializer(instance.user).data
        return rep

    def get_loan_calculation(self, instance):
        total_amount = loan_calculator(instance.amount, instance.fee, instance.tenure)
        loan_amount = {
            'per_month_emi': f'$ {total_amount}',
            'total_amount': f'$ {total_amount*instance.tenure}',
            'net_profit': f'$ {(total_amount*instance.tenure)-instance.amount}'
        }
        return loan_amount

class LoanCalculationSerializer(serializers.ModelSerializer):
    loan_calculation = serializers.SerializerMethodField()
    emi = serializers.SerializerMethodField()
    class Meta:
        model = BorrowerRequestAmount
        fields = ['id', 'amount', 'fee', 'tenure', 'loan_calculation', 'emi']

    def get_loan_calculation(self, instance):
        total_amount = loan_calculator(instance.amount, instance.fee, instance.tenure)
        try:
            admin_commission = LoanManagement.objects.get(id=1)
        except:
            admin_commission = None
        if admin_commission:
            if admin_commission.commission_type == 'PERCENTAGE':
                commission_rate = '%'
                commission = (((total_amount*instance.tenure)-instance.amount)*admin_commission.commission)/100
            else:
                commission = admin_commission.commission
                commission_rate = ''
            loan_amount = {
                'per_month_emi': f'${total_amount}',
                'total_amount': f'${total_amount*instance.tenure}',
                'commission_type': admin_commission.commission_type,
                'commission_rate': f'{admin_commission.commission}{commission_rate}',
                'total_profit': f'${format(((total_amount*instance.tenure)-instance.amount), ".2f")}',
                'admin_commission': f"${format(commission, '.2f')}",
                'net_profit': f'${format(((total_amount*instance.tenure)-instance.amount)-commission, ".2f")}'
            }
            return loan_amount
        else:
            return '0'
    
    def get_emi(self, instance):
        total_amount = loan_calculator(instance.amount, instance.fee, instance.tenure)
        emi = {}
        for i, k in enumerate(range(1, instance.tenure+1), start=1):
            month_name = (date.today() + relativedelta(months=+i-1)).strftime(r"%d-%b-%y")
            emi[f'{month_name}'] = f'${total_amount}x{str(i)}=${total_amount*i}'
        return emi

class BidRequestAcceptRejectSerializer(serializers.Serializer):
    bid_id = serializers.CharField()
    request_type = serializers.CharField()

class EMICalculationSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    tenure = serializers.IntegerField()
    fee = serializers.FloatField()
    start_date = serializers.CharField()
    loan_calculation = serializers.SerializerMethodField()
    emi = serializers.SerializerMethodField()

    def get_loan_calculation(self, instance):
        total_amount = loan_calculator(instance['amount'], instance['fee'], instance['tenure'])
        extra_days_interest = calculate_extra_days_interest(start_date=instance['start_date'], amount=total_amount, tenure=instance["tenure"])
        loan_amount = {
            'per_month_emi': f'${format(total_amount+extra_days_interest["extra_days_interest"], ".2f")}',
            'interest': f'${round(total_amount*instance["tenure"]+extra_days_interest["amount_interest_before_emi"]-instance["amount"], 2)}',
            'you_will_pay': f'${round(total_amount*instance["tenure"]+extra_days_interest["amount_interest_before_emi"], 2)}',
        }
        return loan_amount
    
    def get_emi(self, instance):
        list_data = []
        total_amount = loan_calculator(instance["amount"], instance["fee"], instance["tenure"])
        extra_days_interest = calculate_extra_days_interest(start_date=instance['start_date'], amount=total_amount, tenure=instance["tenure"])
        for i, k in enumerate(range(1, instance["tenure"]+1), start=1):
            emi = {}
            month_name = (datetime.strptime(instance['start_date'], '%Y-%m-%d').date() + relativedelta(months=+i-1)).strftime(r"%d-%b-%y")
            price_data = f'${format(total_amount+extra_days_interest["extra_days_interest"], ".2f")}x{str(i)}=${format((total_amount+extra_days_interest["extra_days_interest"])*i, ".2f")}'
            emi['emi_date'] = month_name
            emi['emi_price'] = price_data
            list_data.append(emi)
        return list_data


class LenderBidingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Biding
        fields = ['fee', 'time_limit', 'created']

class LenderBidingDataSerializer(serializers.ModelSerializer):
    lender = serializers.SerializerMethodField()
    class Meta:
        model = Biding
        fields = "__all__"

    def get_lender(self, instance):
        return UserInformationSerializer(instance.lender).data
    

class BidRequestListForBorrowerSerializer(serializers.ModelSerializer):
    borrower = serializers.SerializerMethodField()
    request_type = serializers.SerializerMethodField()
    class Meta:
        model = BidRequest
        fields = ["id", "borrower", "status", "amount", "tenure", "fee", "slug", "completed_date", "created", "request_type"] #"__all__"

    def get_borrower(self, instance):
        return UserInformationSerializer(instance.borrower).data
    
    def get_request_type(self, instance):
        return "BID"

class BidRequestListForLenderSerializer(serializers.ModelSerializer):
    bid = serializers.SerializerMethodField()
    class Meta:
        model = BorrowerRequestAmount
        fields = ["bid", "request_type"]

    def get_bid(self, instance):
        return BidRequestListForBorrowerSerializer(instance.bid).data
    
