from superadmin.models import *
from rest_framework import serializers
import stripe

class CardTokenSerializer(serializers.Serializer):
    card_token = serializers.CharField()
    card_holder_name = serializers.CharField()

class CardTokenUpdateSerializer(serializers.Serializer):
    card_holder_name = serializers.CharField()
    card_id = serializers.CharField()

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'is_subscribed', 'name', 'original_price', 'interval', 'recurring_type', 'description']

    def get_is_subscribed(self, instance):
        if UserSubscription.objects.filter(user_id=self.context.get('user')).exists():
            if not instance.is_free:
                return True
            else:
                return False
        else:
            return False

class DefaultCardSerializer(serializers.Serializer):
    card_id = serializers.CharField()

class SubscriptionCheckoutSerializer(serializers.Serializer):
    plan_id = serializers.CharField()

class StoreSubscriptionPlanSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    class Meta:
        model = StoreSubscriptionPlan
        fields = ['id', 'is_subscribed', 'name', 'price', 'interval', 'description']

    def get_is_subscribed(self, instance):
        if StoreSubscription.objects.filter(user_id=self.context.get('user')).exists():
            return True
        else:
            return False

class TransferAmountBankSerializer(serializers.Serializer):
    amount = serializers.CharField()    
    bank_id = serializers.CharField() 