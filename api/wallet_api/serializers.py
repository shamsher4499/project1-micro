from superadmin.models import *
from rest_framework import serializers

class LenderAddAmountSerializer(serializers.Serializer):
    amount = serializers.CharField()

class LenderWalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LenderWalletTransaction
        fields = '__all__'