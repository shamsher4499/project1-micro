from superadmin.models import *
from rest_framework import serializers
from datetime import datetime, timedelta

class ActiveLoanSerializer(serializers.ModelSerializer):
    lender_info = serializers.SerializerMethodField()
    borrower_info = serializers.SerializerMethodField()
    next_emi_date = serializers.SerializerMethodField()
    amount_left = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    class Meta:
        model = BorrowerRequestAmount
        fields = ['id', 'user_type', 'request_type', 'amount', 'tenure', 'fee', 'approve_date', 'next_emi_date', 'amount_left', 'lender_info', 'borrower_info']

    def get_lender_info(self, instance):
        if 'LENDER' == self.context.get('user_type'):
            if BorrowerRequestAmount.objects.filter(lender_id=self.context.get('user')).exists():
                user_data = User.objects.get(id=self.context.get('user'))
                data = {'name':user_data.name, 'profile_pic':user_data.profile_pic.url if user_data.profile_pic else None}
                return data
            return None
        
        if 'BORROWER' == self.context.get('user_type'):
            user_data = BorrowerRequestAmount.objects.get(id=instance.id)
            data = {'name':user_data.lender.name, 'profile_pic':user_data.lender.profile_pic.url if user_data.lender.profile_pic else None}
            return data
        
        
    def get_borrower_info(self, instance):
        if 'BORROWER' == self.context.get('user_type'):
            user_data = BorrowerRequestAmount.objects.get(id=instance.id)
            data = {'name':user_data.user.name, 'profile_pic':user_data.user.profile_pic.url if user_data.user.profile_pic else None}
            return data
        
        if 'LENDER' == self.context.get('user_type'):
            user_data = BorrowerRequestAmount.objects.get(id=instance.id)
            data = {'name':user_data.user.name, 'profile_pic':user_data.user.profile_pic.url if user_data.user.profile_pic else None}
            return data
        
    def get_next_emi_date(self, instance):
        if instance.approve_date:
            return instance.approve_date + timedelta(days=30)
        else:
            return datetime.now() + timedelta(days=30)
    
    def get_amount_left(self, instance):
        return 5000
    
    def get_user_type(self, instance):
        return self.context.get('user_type')
    
class TransferLoanUserSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    class Meta:
        model = ContactList
        fields = ['id', 'mobile_number', 'user_info', 'created']

    def get_user_info(self, instance):
        user = User.objects.get(mobile=instance.mobile_number)
        user_data = {
            'id':user.id,
            'name': user.name,
            'profile_pic': user.profile_pic if user.profile_pic else None
        }
        return user_data

class TransferLoanRequestSerializer(serializers.Serializer):
    user_list = serializers.CharField()
    loan_id = serializers.CharField()

class TransferLoanRequestViewSerializer(serializers.ModelSerializer):
    loan_info = serializers.SerializerMethodField()
    class Meta:
        model = TransferLoanRequest
        fields = ['id', 'loan_info', 'approve', 'created']

    
    def get_loan_info(self, instance):
        loan = BorrowerRequestAmount.objects.get(id=instance.loan_id)
        loan_data = {
            'id':loan.id,
            'amount': loan.amount,
            'request_type': loan.request_type,
            'next_emi_date': datetime.now() + timedelta(days=30),
            'tenure': loan.tenure,
            'fee': loan.fee,
            'amount_left': 5000,
            'lender_name': loan.lender.name,
            'approve_date': loan.approve_date,
            'created': loan.created,
        }
        return loan_data

class TransferLoanRequestStatusSerializer(serializers.ModelSerializer):
    # loan_info = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    class Meta:
        model = TransferLoanRequestUser
        fields = ['id', 'user_info', 'status', 'approve', 'created']

    def get_user_info(self, instance):
        user = User.objects.get(id=instance.transfer_user_id)
        user_data = {
            'id':user.id,
            'name': user.name,
            'profile_pic': user.profile_pic if user.profile_pic else None
        }
        return user_data
    
    def get_status(self, instance):
        loan = BorrowerRequestAmount.objects.get(id=instance.loan_id)
        if loan.approve:
            return 'pending'
        return 'approved'
    
    # def get_loan_info(self, instance):
    #     loan = BorrowerRequestAmount.objects.get(id=instance.loan_id)
    #     loan_data = {
    #         'id':loan.id,
    #         'amount': loan.amount,
    #         'request_type': loan.request_type,
    #         'tenure': loan.tenure,
    #         'fee': loan.fee,
    #         'lender_name': loan.lender.name,
    #         'approve_date': loan.approve_date,
    #         'created': loan.created,
    #     }
    #     return loan_data

class EmiScheduleSerializer(serializers.ModelSerializer):
    # loan_info = serializers.SerializerMethodField()
    class Meta:
        model = LoanEMISchedule
        fields = ['id', 'received_amount', 'pending_amount', 'emi_amount', 'emi_date', 'status']


class LendingBoxActiveLoanSerializer(serializers.ModelSerializer):
    lender_info = serializers.SerializerMethodField()
    borrower_info = serializers.SerializerMethodField()
    next_emi_date = serializers.SerializerMethodField()
    amount_left = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    class Meta:
        model = StoreLoanEmi
        # fields = '__all__'
        fields = ['id', 'user_type', 'amount', 'loan_type', 'tenure', 'fee', 'approve_date', 'next_emi_date', 'amount_left', 'lender_info', 'borrower_info']

    def get_lender_info(self, instance):
        if 'LENDING_BOX' == self.context.get('user_type'):
            if StoreLoanEmi.objects.filter(store_id=self.context.get('user')).exists():
                user_data = User.objects.get(id=self.context.get('user'))
                data = {'name':user_data.name, 'profile_pic':user_data.profile_pic.url if user_data.profile_pic else None}
                return data
            return None
        
        if 'BORROWER' == self.context.get('user_type'):
            user_data = StoreLoanEmi.objects.get(id=instance.id)
            data = {'name':user_data.store.name, 'profile_pic':user_data.store.profile_pic.url if user_data.store.profile_pic else None}
            return data
        
        
    def get_borrower_info(self, instance):
        if 'BORROWER' == self.context.get('user_type'):
            user_data = StoreLoanEmi.objects.get(id=instance.id)
            data = {'name':user_data.user.name, 'profile_pic':user_data.user.profile_pic.url if user_data.user.profile_pic else None}
            return data
        
        if 'LENDING_BOX' == self.context.get('user_type'):
            user_data = StoreLoanEmi.objects.get(id=instance.id)
            data = {'name':user_data.user.name, 'profile_pic':user_data.user.profile_pic.url if user_data.user.profile_pic else None}
            return data
        
    def get_next_emi_date(self, instance):
        if instance.approve_date:
            return instance.approve_date + timedelta(days=30)
        else:
            return datetime.now() + timedelta(days=30)
    
    def get_amount_left(self, instance):
        return 5000
    
    def get_user_type(self, instance):
        return self.context.get('user_type')
    
class LendingBoxCompletedLoanSerializer(serializers.ModelSerializer):
    lender_info = serializers.SerializerMethodField()
    borrower_info = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    class Meta:
        model = StoreLoanEmi
        # fields = '__all__'
        fields = ['id', 'user_type', 'amount', 'loan_type', 'tenure', 'fee', 'approve_date', 'completed_date', 'lender_info', 'borrower_info']

    def get_lender_info(self, instance):
        if 'LENDING_BOX' == self.context.get('user_type'):
            if StoreLoanEmi.objects.filter(store_id=self.context.get('user')).exists():
                user_data = User.objects.get(id=self.context.get('user'))
                data = {'name':user_data.name, 'profile_pic':user_data.profile_pic.url if user_data.profile_pic else None}
                return data
            return None
        
        if 'BORROWER' == self.context.get('user_type'):
            user_data = StoreLoanEmi.objects.get(id=instance.id)
            data = {'name':user_data.store.name, 'profile_pic':user_data.store.profile_pic.url if user_data.store.profile_pic else None}
            return data
        
        
    def get_borrower_info(self, instance):
        if 'BORROWER' == self.context.get('user_type'):
            user_data = StoreLoanEmi.objects.get(id=instance.id)
            data = {'name':user_data.user.name, 'profile_pic':user_data.user.profile_pic.url if user_data.user.profile_pic else None}
            return data
        
        if 'LENDING_BOX' == self.context.get('user_type'):
            user_data = StoreLoanEmi.objects.get(id=instance.id)
            data = {'name':user_data.user.name, 'profile_pic':user_data.user.profile_pic.url if user_data.user.profile_pic else None}
            return data
    
    def get_user_type(self, instance):
        return self.context.get('user_type')