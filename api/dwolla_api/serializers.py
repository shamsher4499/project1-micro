from superadmin.models import *
from rest_framework import serializers

class DwollaCustomerSerializer(serializers.Serializer):
    firstName = serializers.CharField()
    lastName = serializers.CharField()
    email = serializers.CharField()
    type = serializers.CharField()
    address1 = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    postalCode = serializers.CharField()
    dateOfBirth = serializers.CharField()
    ssn = serializers.CharField()

class FundingSourceSerializer(serializers.Serializer):
    routingNumber = serializers.CharField()
    accountNumber = serializers.CharField()
    bankAccountType = serializers.CharField()
    name = serializers.CharField()

class TransferSerializer(serializers.Serializer):
    amount = serializers.CharField()
    funding_source = serializers.CharField()
    # destination_source = serializers.CharField()

class CheckBalanceSerializer(serializers.Serializer):
    source_id = serializers.CharField()

class TransactionStatusSerializer(serializers.Serializer):
    transaction_id = serializers.CharField()

class VerifyFundingSourceSerializer(serializers.Serializer):
    funding_id = serializers.CharField()

class VerifyAmountSerializer(serializers.Serializer):
    funding_id = serializers.CharField()
    amount_1 = serializers.CharField()
    amount_2 = serializers.CharField()