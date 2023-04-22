from django.db import models
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import slugify
from .manager import *
from django.conf import settings
from .choices import *
import png
import pyqrcode
from random import randint
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import os
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
import jsonfield
# Create your models here.

def generateNumber(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

class BaseModel(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract=True

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profile/', null=True, blank=True)
    qr_code = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    otp = models.CharField(max_length=6 ,null=True, blank=True)
    mobile_verification_otp = models.CharField(max_length=6 ,null=True, blank=True)
    document = models.FileField(upload_to='documents/', null=True, blank=True)
    notification_settings = models.BooleanField(default=False, null=True, blank=True)
    location_settings = models.BooleanField(default=False, null=True, blank=True)
    latitude = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.CharField(max_length=255, null=True, blank=True)
    customer_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    provider_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    provider_name = models.CharField(max_length=255, null=True, blank=True)
    fcm_token = models.CharField(max_length=255, unique=False, null=True, blank=True)
    is_verified = models.BooleanField(default=False, null=True, blank=True)
    mobile_verified = models.BooleanField(default=False, null=True, blank=True)
    is_active = models.BooleanField(default=False, null=True, blank=True)
    is_store = models.BooleanField(default=False, null=True, blank=True)
    otp_count = models.CharField(max_length=10, default=0, null=True, blank=True)
    login_count = models.IntegerField(default=0, null=True, blank=True)
    email_sent = models.BooleanField(default=False, null=True, blank=True)
    session_login = models.BooleanField(default=False)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    calling_code = models.CharField(max_length=10, null=True, blank=True)
    social_security_number = models.CharField(max_length=9, null=True, blank=True)
    login_attempt_time = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    otp_sent_time = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_modified = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    slug = models.TextField(unique=True, null=True, blank=True)
    slug_user = models.CharField(max_length=50, unique=True, default=uuid.uuid4)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save_with_slug(self):
        refresh = RefreshToken.for_user(User)
        self.slug = str(refresh.access_token)
        super().save()
        self.save_qrcode()
    
    def save_qrcode(self, *args):
        # my_dict = {"user_key": user_profile.slug}
        url = pyqrcode.create(settings.WEBSITE_URL+reverse('request_otp_profile', args=[self.slug_user]))
        qr_code = f'media/qrcode/{self.slug_user}.png'
        self.qr_code = qr_code 
        url.png(qr_code, scale=8)
        UserProfileLenderBox.objects.create(user_id=self.id, name=self.name, slug=self.slug_user)
    
@receiver(models.signals.post_delete, sender=User)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.profile_pic and os.path.isfile(instance.profile_pic.path):
        os.remove(instance.profile_pic.path)
    if instance.document and os.path.isfile(instance.document.path):
        os.remove(instance.document.path)
    if instance.qr_code and os.path.isfile(instance.qr_code):
        os.remove(instance.qr_code)

@receiver(models.signals.pre_save, sender=User)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.id:
        return False  
    try:
        user = User.objects.get(id=instance.id)
    except User.DoesNotExist:
        return False
    old_profile_pic = user.profile_pic
    old_document = user.document
    new_profile_pic = instance.profile_pic
    new_document = instance.document
    if old_profile_pic and old_profile_pic != new_profile_pic and os.path.isfile(old_profile_pic.path):
        os.remove(old_profile_pic.path)
    if old_document and not old_document == new_document and os.path.isfile(old_document.path):
        os.remove(old_document.path)

class StoreProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    store_name = models.CharField(max_length=255, null=True, blank=True)
    dob = models.DateField(auto_now_add=False, null=True, blank=True)
    tax_id = models.CharField(max_length=9, null=True, blank=True)
    rating = models.IntegerField(default=0, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    business_type = models.CharField(max_length=255, choices=BUSINESS_TYPE, null=True, blank=True)
    store_category = models.CharField(max_length=255, choices=CATEGORY_TYPE, default='NEW')
    avg_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    interval_month = models.IntegerField(default=0, null=True, blank=True)
    interest = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    about_us = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

    def get_review_count(self):
        return StoreRating.objects.filter(store_id=self.user).count()

class SocialAccount(models.Model):
    facebook = models.CharField(max_length=255, null=True, blank=True)
    instagram = models.CharField(max_length=255, null=True, blank=True)
    youtube = models.CharField(max_length=255, null=True, blank=True)
    twitter = models.CharField(max_length=255, null=True, blank=True)
    linkedin = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class Testimonial(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='testimonial/', null=True, blank=True)
    desc = models.CharField(max_length=255, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

@receiver(models.signals.post_delete, sender=Testimonial)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

@receiver(models.signals.pre_save, sender=Testimonial)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.id:
        return False

    try:
        old_file = Testimonial.objects.get(id=instance.id).image
    except Testimonial.DoesNotExist:
        return False

    new_file = instance.image
    if old_file and not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

class EmailTemplate(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    editor = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class AppIntro(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='App-intro/', null=True, blank=True)
    desc = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

@receiver(models.signals.post_delete, sender=AppIntro)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

@receiver(models.signals.pre_save, sender=AppIntro)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.id:
        return False

    try:
        old_file = AppIntro.objects.get(id=instance.id).image
    except AppIntro.DoesNotExist:
        return False

    new_file = instance.image
    if old_file and not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

class ContactUs(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True, unique=False)
    subject = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=250, choices=QUERY_STATUS, default='PENDING')
    reply_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class LenderWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    wallet_id = models.CharField(max_length=50, unique=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=250, choices=WALLET_STATUS, default='ACTIVE')
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class BorrowerWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=250, choices=WALLET_STATUS, default='ACTIVE')
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class LenderWalletTransaction(models.Model):
    wallet = models.ForeignKey(LenderWallet, on_delete=models.CASCADE, related_name='wallet', null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=250, choices=AMOUNT_STATUS, null=True)
    payment_by = models.CharField(max_length=250, null=True, default='ADD MONEY')
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class BorrowerWalletTransaction(models.Model):
    wallet = models.ForeignKey(BorrowerWallet, on_delete=models.CASCADE, related_name='wallet', null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=250, choices=AMOUNT_STATUS, null=True)
    payment_by = models.CharField(max_length=250, null=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class BidRequest(models.Model):
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=255, default="PENDING", null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tenure = models.IntegerField(null=True, blank=True)
    fee = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    completed_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class BorrowerRequestAmount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lender', null=True)
    bid = models.ForeignKey(BidRequest, on_delete=models.CASCADE, related_name='bid_request', null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    request_type = models.CharField(max_length=250, choices=REQUEST_TYPE, null=True)
    tenure = models.IntegerField(null=True, blank=True)
    fee = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    approve = models.BooleanField(default=False, null=True, blank=True)
    completed = models.BooleanField(default=False, null=True, blank=True)
    waive_off = models.BooleanField(default=False, null=True, blank=True)
    reject = models.BooleanField(default=False, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    approve_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    completed_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    transfer_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class ContactList(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    mobile_number = models.CharField(max_length=250, null=True)

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    address_title = models.CharField(max_length=250, null=True)
    address = models.CharField(max_length=250, null=True)
    area = models.CharField(max_length=250, null=True)
    city = models.CharField(max_length=250, null=True)
    state = models.CharField(max_length=250, null=True)
    zipcode = models.IntegerField(null=True, blank=True)
    landmark = models.CharField(max_length=250, null=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    calling_code = models.CharField(max_length=10, null=True, blank=True)
    phone_number = models.CharField(max_length=250, null=True)
    is_default = models.BooleanField(default=False, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class Blog(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True, unique=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    image = models.ImageField(upload_to='blog/', null=True, blank=True)
    desc = models.TextField(null=True, blank=True)
    blog_slug = models.SlugField()
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.blog_slug = slugify(self.name)
        super(Blog, self).save(*args, **kwargs)

class AboutUs(BaseModel):
    image1 = models.ImageField(upload_to='about-us/', null=True, blank=True)
    image2 = models.ImageField(upload_to='about-us/', null=True, blank=True)
    image3 = models.ImageField(upload_to='about-us/', null=True, blank=True)
    desc1 = models.TextField(null=True, blank=True)
    desc2 = models.TextField(null=True, blank=True)
    desc3 = models.TextField(null=True, blank=True)

class TermsCondition(BaseModel):
    desc = models.TextField(null=True, blank=True)

class PrivacyPolicy(BaseModel):
    desc = models.TextField(null=True, blank=True)

class YoutubeVideoID(models.Model):
    youtube_id = models.TextField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='homepage/', null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)

class WebHomePage(BaseModel):
    image1 = models.ImageField(upload_to='homepage-body/', null=True, blank=True)
    image2 = models.ImageField(upload_to='homepage-body/', null=True, blank=True)
    image3 = models.ImageField(upload_to='homepage-body/', null=True, blank=True)
    image4 = models.ImageField(upload_to='homepage-body/', null=True, blank=True)
    image5 = models.ImageField(upload_to='homepage-body/', null=True, blank=True)
    name2 = models.CharField(max_length=254, null=True, blank=True)
    name3 = models.CharField(max_length=254, null=True, blank=True)
    name4 = models.CharField(max_length=254, null=True, blank=True)
    name5 = models.CharField(max_length=254, null=True, blank=True)
    desc1 = models.TextField(null=True, blank=True)
    desc2 = models.TextField(null=True, blank=True)
    desc3 = models.TextField(null=True, blank=True)
    desc4 = models.TextField(null=True, blank=True)
    desc5 = models.TextField(null=True, blank=True)

class WalletAmountLimit(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    
class FAQ(BaseModel):
    answer = models.TextField(null=True, blank=True)

class LoanManagement(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interest = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    tenure_month = models.IntegerField(default=1, null=True, blank=True)
    loan_request = models.IntegerField(default=1, null=True, blank=True)
    loan_reject = models.IntegerField(default=1, null=True, blank=True)
    blocked_days = models.IntegerField(default=1, null=True, blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_type = models.CharField(max_length=15, choices=COMMISSION_TYPE, default='FIXED_PRICE')
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    last_modified = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
class BlockEmailDomain(BaseModel):
    domain = models.CharField(max_length=255, null=True, blank=True)

class PlanFeature(BaseModel):
    is_premium = models.BooleanField(default=False, null=True, blank=True)

class SubscriptionPlan(BaseModel):
    price_id = models.CharField(max_length=255, null=True, blank=True)
    product_id = models.CharField(max_length=255, null=True, blank=True)
    original_price = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    offer_price = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    is_offer = models.BooleanField(default=False, null=True, blank=True)
    is_free = models.BooleanField(default=False, null=True, blank=True)
    interval = models.CharField(max_length=15, choices=INTERVAL_TYPE, default='MONTHLY')
    recurring_type = models.CharField(max_length=15, choices=RECURRING_TYPE, default='AUTO')
    description = models.TextField(null=True, blank=True)

class UserProfileLenderBox(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    otp = models.IntegerField(default=0, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class StoreTier(BaseModel):
    starting_price = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    end_price = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    interval_month = models.IntegerField(default=0, null=True, blank=True)
    interest = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    category = models.CharField(max_length=15, choices=TIER_TYPE, default='TIER 1')
    description = models.TextField(null=True, blank=True)

class StoreSubscriptionPlan(BaseModel):
    price_id = models.CharField(max_length=255, null=True, blank=True)
    product_id = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    interval = models.CharField(max_length=15, choices=INTERVAL_TYPE, default='MONTHLY')
    recurring_type = models.CharField(max_length=15, choices=RECURRING_TYPE, default='AUTO')
    description = models.TextField(null=True, blank=True)

class StoreRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    store = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store', null=True)
    rating = models.IntegerField(default=0, null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class CardToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=100, null=True, blank=True)
    card_id = models.CharField(max_length=100, null=True, blank=True)
    default_payment = models.BooleanField(default=False)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    subscription_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    plan = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class StoreSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    subscription_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    plan = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class StoreTiming(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_id', null=True, blank=True)
    timing = jsonfield.JSONField(null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class DwollaCustomer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dwolla_user', null=True, blank=True)
    dwolla_id = models.CharField(max_length=50, unique=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class DwollaBankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dwolla_id', null=True, blank=True)
    dwolla = models.ForeignKey(DwollaCustomer, on_delete=models.CASCADE, related_name='user_bank', null=True, blank=True)
    funding_source_id = models.CharField(max_length=50, unique=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class TransferLoanRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='request_user', null=True)
    loan = models.ForeignKey(BorrowerRequestAmount, on_delete=models.CASCADE, null=True)
    reject = models.BooleanField(default=False, null=True, blank=True)
    approve = models.BooleanField(default=False, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class TransferLoanRequestUser(models.Model):
    transfer = models.ForeignKey(TransferLoanRequest, on_delete=models.CASCADE, related_name='transfer_loan_table', null=True)
    transfer_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfer_user', null=True)
    loan = models.ForeignKey(BorrowerRequestAmount, on_delete=models.CASCADE, null=True)
    reject = models.BooleanField(default=False, null=True, blank=True)
    approve = models.BooleanField(default=False, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class AdminAccount(models.Model):
    wallet_id = models.CharField(max_length=50, unique=True, blank=True)
    dwolla_id = models.CharField(max_length=50, unique=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class AdminEarning(models.Model):
    loan = models.OneToOneField(BorrowerRequestAmount, on_delete=models.CASCADE, unique=True, null=True)
    received_amount = models.CharField(max_length=50, default='0', blank=True)
    pending_amount = models.CharField(max_length=50, blank=True)
    emi = models.CharField(max_length=50, default='0', blank=True)
    status = models.CharField(max_length=50, default='PENDING', blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class LoanEMISchedule(models.Model):
    loan = models.ForeignKey(BorrowerRequestAmount, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    received_amount = models.CharField(max_length=50, default='0', blank=True)
    pending_amount = models.CharField(max_length=50, blank=True)
    emi_amount = models.CharField(max_length=50, default='0', blank=True)
    emi_date = models.DateField(auto_now_add=False, null=True)
    status = models.CharField(max_length=50, default='PENDING', blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

class StoreLoanEmi(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    store = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_loan', null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loan_type = models.CharField(max_length=250, choices=LOAN_TYPE, null=True)
    tenure = models.IntegerField(null=True, blank=True)
    fee = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    approve = models.BooleanField(default=False, null=True, blank=True)
    completed = models.BooleanField(default=False, null=True, blank=True)
    waive_off = models.BooleanField(default=False, null=True, blank=True)
    reject = models.BooleanField(default=False, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    approve_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    time_limit = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    completed_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

class Biding(models.Model):
    bid = models.ForeignKey(BidRequest, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bid_lender', null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tenure = models.IntegerField(null=True, blank=True)
    fee = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    user_approve = models.BooleanField(default=False, null=True, blank=True)
    lender_approve = models.BooleanField(default=False, null=True, blank=True)
    user_lock = models.BooleanField(default=False, null=True, blank=True)
    lender_lock = models.BooleanField(default=False, null=True, blank=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    time_limit = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)