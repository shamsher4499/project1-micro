from superadmin.models import *
from rest_framework import serializers
from api.auth_api.serializers import UserSerializer
from numerize.numerize import numerize
import json

class StoreRegisterSerializer(serializers.Serializer):
    email = serializers.CharField()
    firstName = serializers.CharField(required=True)
    lastName = serializers.CharField(required=True)
    type = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    postalCode = serializers.CharField(required=True)
    mobile = serializers.CharField()
    password = serializers.CharField()
    store_name = serializers.CharField()
    dob = serializers.CharField()
    ein_number = serializers.CharField()
    address = serializers.CharField()
    avg_ticket = serializers.CharField()
    business_type = serializers.CharField()
    country_code = serializers.CharField()
    calling_code = serializers.CharField()
    social_security_number = serializers.CharField()


class StoreAvgTicketSerializer(serializers.Serializer):
    avg_amount = serializers.CharField()
    surcharge = serializers.CharField()
    loan_tenure = serializers.CharField()

class UserSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'owner_name', 'email', 'mobile', 'profile_pic', 'qr_code', 'document', 'country_code', 
        'calling_code', 'notification_settings', 'location_settings', 'latitude', 'longitude', 'is_verified', 
        'fcm_token', 'mobile_verified', 'created', 'last_login']

    def get_owner_name(self, instance):
        return instance.name

class StoreRatingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = StoreRating
        fields = ['id', 'rating', 'review', 'user']

    def get_user(self, instance):
        user = User.objects.get(email=instance.user)
        user_data = {
            'name':user.name,
            'profile_pic':user.profile_pic.url if user.profile_pic else None,
            }
        return user_data

class StorePersonalProfileSerializer(serializers.Serializer):
    profile_pic = serializers.ImageField(required=False)
    store_name = serializers.CharField()
    mobile = serializers.CharField()
    calling_code = serializers.CharField()
    country_code = serializers.CharField()
    about_us = serializers.CharField()
    owner_name = serializers.CharField()
    address = serializers.CharField()
    ein_number = serializers.CharField()
    dob = serializers.CharField()
    business_type = serializers.CharField()

class StoreTimingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreTiming
        fields = ['timing']

class StoreProfileSerializer(serializers.ModelSerializer):
    personal_data = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()
    rating_and_reviews = serializers.SerializerMethodField()
    amount_distribution = serializers.SerializerMethodField()
    register_since = serializers.SerializerMethodField()
    is_rated = serializers.SerializerMethodField()
    store_timing = serializers.SerializerMethodField()
    class Meta:
        model = StoreProfile
        fields = ['id', 'is_rated', 'personal_data', 'amount_distribution', 'about_us', 'rating', 'review', 'rating_and_reviews', 
        'store_name', 'dob', 'tax_id', 'address', 'store_category', 'business_type', 'register_since', 'store_timing']
    
    def get_personal_data(self, instance):
        data = User.objects.get(id=instance.user_id)
        return UserSerializer(data).data
    
    def get_review(self, instance):
        data = StoreRating.objects.filter(store_id=instance.user_id)
        if data:
            return data.count()
        else:
            return 0

    def get_rating_and_reviews(self, instance):
        data = StoreRating.objects.filter(store_id=instance.user_id)
        return StoreRatingSerializer(data, many=True).data

    def get_amount_distribution(self, instance):
        return f'${numerize(12_00_000)}'

    def get_register_since(self, instance):
        return instance.created.year

    def get_is_rated(self, instance):
        if StoreRating.objects.filter(user_id=self.context.get('user'), store_id=self.get_personal_data(instance)['id']).exists():
            return True
        return False

    def get_store_timing(self, instance):
        store_timing = StoreTiming.objects.all()
        if store_timing.filter(user_id=instance.user_id).exists():
            store_data = store_timing.get(user_id=instance.user_id)
            return store_data.timing
        else:
            return None
        
class StoreLoanSerializer(serializers.Serializer):
    amount = serializers.CharField()
    loan_type = serializers.CharField()
    user_id = serializers.CharField()

class StoreLoanRequestSerializer(serializers.Serializer):
    request_type = serializers.CharField()
    loan_id = serializers.CharField()


class StoreLoanViewSerializer(serializers.ModelSerializer):
    borrower = serializers.SerializerMethodField()
    store = serializers.SerializerMethodField()
    class Meta:
        model = StoreLoanEmi
        fields = ['id', 'amount', 'loan_type', 'tenure', 'fee', 'borrower', 'store']

    def get_borrower(self, instance):
        user_data = User.objects.get(id=instance.user_id)
        return {
            'name':user_data.name,
            'profile_pic':user_data.profile_pic.url if user_data.profile_pic else None,    
            }
    
    def get_store(self, instance):
        user_data = User.objects.get(id=instance.store_id)
        return {
            'name':user_data.name,
            'profile_pic':user_data.profile_pic.url if user_data.profile_pic else None,    
            }