from superadmin.models import *
from rest_framework import serializers


class FundingSourceSerializer(serializers.Serializer):
    account_id = serializers.CharField()    
    public_token = serializers.CharField() 
    bank_name = serializers.CharField() 