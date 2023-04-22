from superadmin.models import *
from rest_framework import serializers


class StoreProfileSerializer(serializers.ModelSerializer):
    review = serializers.SerializerMethodField()
    loan_period = serializers.SerializerMethodField()
    surcharge = serializers.SerializerMethodField()
    store_timing = serializers.SerializerMethodField()
    class Meta:
        model = StoreProfile
        fields = ['avg_amount', 'loan_period', 'surcharge', 'rating', 'review', 'store_name', 'dob', 'tax_id', 
        'address', 'store_category', 'business_type', 'about_us', 'store_timing',]
    
    def get_review(self, instance):
        data = StoreRating.objects.filter(store_id=instance.user_id)
        if data:
            return data.count()
        else:
            return 0

    def get_loan_period(self, instance):
        return instance.interval_month

    def get_surcharge(self, instance):
        return f'{instance.interest}%'

    def get_store_timing(self, instance):
        store_timing = StoreTiming.objects.get(user_id=instance.user_id)
        return store_timing.timing

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    firstName = serializers.CharField(required=True)
    lastName = serializers.CharField(required=True)
    type = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    postalCode = serializers.CharField(required=True)
    dateOfBirth = serializers.CharField(required=True)
    mobile = serializers.CharField(required=True)
    document = serializers.FileField(required=True)
    country_code = serializers.CharField(required=True)
    calling_code = serializers.CharField(required=True)
    social_security_number = serializers.CharField(required=True)
    
    # class Meta:
    #     model = User
    #     fields = ['email', 'password', 'name', 'mobile', 'document', 'country_code', 'calling_code']
    #     extra_kwargs = {
    #         'password': {'write_only': True}
    #     }

class ProfileSerializer(serializers.Serializer):
    name = serializers.CharField()
    mobile = serializers.CharField()
    country_code = serializers.CharField()
    calling_code = serializers.CharField()
    social_security_number = serializers.CharField()

class NotificationSettingsSerializer(serializers.Serializer):
    notification = serializers.CharField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    # fcm_token = serializers.CharField(required=False, allow_blank=True)

class UserSerializer(serializers.ModelSerializer):
    store_information = serializers.SerializerMethodField()
    subscription_features = serializers.SerializerMethodField()
    is_premium_user = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'mobile', 'profile_pic', 'social_security_number', 'qr_code', 'document', 'country_code', 
        'calling_code', 'notification_settings', 'location_settings', 'latitude', 'longitude', 'is_verified', 
        'fcm_token', 'mobile_verified', 'created', 'last_login', 'is_premium_user', 'subscription_features', 'store_information']

    def get_store_information(self, instance):
        if instance.is_store:
            store = StoreProfile.objects.get(user_id=instance.id)
            return StoreProfileSerializer(store).data
        else:
            return None

    def get_subscription_features(self, instance):
        data = {'cashuu_score': False, 'transfer_loan_request': False}
        if UserSubscription.objects.filter(user_id=instance.id).exists():
            return {'cashuu_score': True, 'transfer_loan_request': True}
        else:
            return data
        
    def get_is_premium_user(self, instance):
        if UserSubscription.objects.filter(user_id=self.context.get('user_id')).exists():
            return True
        return False
        
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.CharField(required=False)
    mobile = serializers.CharField(required=False)

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=False)
    password = serializers.CharField()
    fcm_token = serializers.CharField()
    # is_store = serializers.CharField()
    mobile = serializers.CharField(required=False)

class PasswordResetSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

class ChangePasswordEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ChangePasswordVerifyEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

class MobileNumberVerifySerializer(serializers.Serializer):
    # email = serializers.EmailField()
    mobile = serializers.CharField()
    calling_code = serializers.CharField()
    country_code = serializers.CharField()

class MobileNumberOTPVerifySerializer(serializers.Serializer):
    mobile = serializers.CharField()
    otp = serializers.CharField()

class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

class MobileLoginSerializer(serializers.Serializer):
    mobile = serializers.CharField()

class MobileLoginOTPVerifySerializer(serializers.Serializer):
    mobile = serializers.CharField()
    otp = serializers.CharField()

class ChangePasswordMobileSerializer(serializers.Serializer):
    mobile = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

class LenderAddAmountSerializer(serializers.Serializer):
    amount = serializers.CharField()

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class ContactListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactList
        fields = ['id', 'name', 'mobile_number', 'created']

class AppIntroSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppIntro
        fields = ['id', 'title', 'desc', 'image']

class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = '__all__'

class UserInformationSerializer(serializers.ModelSerializer):
    # store_information = serializers.SerializerMethodField()
    # subscription_features = serializers.SerializerMethodField()
    # is_premium_user = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'mobile', 'profile_pic', 'country_code', 'calling_code', 'is_verified', 'created']

    # def get_store_information(self, instance):
    #     if instance.is_store:
    #         store = StoreProfile.objects.get(user_id=instance.id)
    #         return StoreProfileSerializer(store).data
    #     else:
    #         return None

    # def get_subscription_features(self, instance):
    #     data = {'cashuu_score': False, 'transfer_loan_request': False}
    #     if UserSubscription.objects.filter(user_id=instance.id).exists():
    #         return {'cashuu_score': True, 'transfer_loan_request': True}
    #     else:
    #         return data
        
    # def get_is_premium_user(self, instance):
    #     if UserSubscription.objects.filter(user_id=self.context.get('user_id')).exists():
    #         return True
    #     return False