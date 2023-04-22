from django.conf import settings
from datetime import timedelta
from api.dwolla_payment import DwollaTransferAPI
from api.dwolla_payment import check_wallet_amount
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from app.decorators import *
from superadmin.models import *
from .email import *

def home(request):
    template_name = 'frontend/include/body.html'
    blogs = Blog.objects.all().order_by('-id')[:3]
    try:
        youtube = YoutubeVideoID.objects.get(id=1)
        homepage_body = WebHomePage.objects.get(id=1)
    except:
        youtube = None
        homepage_body = None
    faq = FAQ.objects.all()[:4]
    context = {'blogs':blogs, 'youtube':youtube, 'faq':faq, 'homepage_body':homepage_body}
    return render(request, template_name, context)

def privacyPolicy(request):
    template_name = 'frontend/cms/privacy-policy.html'
    policy = PrivacyPolicy.objects.first()
    return render(request, template_name, {'policy':policy})

def termConditions(request):
    template_name = 'frontend/cms/terms-and-conditions.html'
    terms = TermsCondition.objects.first()
    return render(request, template_name, {'terms':terms})

def aboutUs(request):
    template_name = 'frontend/cms/about-us.html'
    teams = Testimonial.objects.all().order_by('-id')[:3]
    about_us = AboutUs.objects.get(id=1)
    context = {'teams':teams, 'about_us':about_us}
    return render(request, template_name, context)

def fAQ(request):
    template_name = 'frontend/cms/faq.html'
    faq = FAQ.objects.all().order_by('-id')
    return render(request, template_name, {'faq':faq})

def blog(request):
    template_name = 'frontend/cms/blog.html'
    blog = Blog.objects.all().order_by('-id')
    return render(request, template_name, {'blog':blog})

def blogDetails(request, slug, blog_slug):
    template_name = 'frontend/cms/blog-details.html'
    blog = Blog.objects.get(slug=slug)
    return render(request, template_name, {'blog':blog})

def contactUs(request):
    template_name = 'frontend/cms/contact-us.html'
    if request.method == 'POST':
        data = request.POST
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        if name.isspace() or name == '':
            messages.error(request, "Please enter name!")
            return render(request, template_name, {'data':data})
        if email.isspace() or email == '' or '@' not in email:
            messages.error(request, "Please enter valid email!")
            return render(request, template_name, {'data':data})
        if subject.isspace() or subject == '':
            messages.error(request, "Please enter subject!")
            return render(request, template_name, {'data':data})
        if message.isspace() or message == '':
            messages.error(request, "Please enter message!")
            return render(request, template_name, {'data':data})
        else:
            inqury = ContactUs.objects.create(name=name, email=email, subject=subject, message=message)
            sendInqury(inqury)
            messages.success(request, "We have received your query. Please wait for the response.")
            return render(request, template_name)
    return render(request, template_name)

@role_required
def userprofile(request):
    user = request.user
    template_name = 'frontend/dashboard/profile.html'
    if request.method == 'POST':
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        image = request.FILES.get('image')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template_name)
        if mobile.isspace() or mobile == '' or len(mobile) != 10 or not mobile.isnumeric():
            messages.error(request, "Mobile can't be blank or Must be 10 digit.")
            return render(request, template_name)
        if image and (image.name.split('.')[-1]).lower() not in ['jpeg', 'jpg', 'png']:
            messages.error(request, "Image must be .jpeg/jpg format.")
            return render(request, template_name)
        user.name = name
        if user.mobile != mobile:
            user.mobile = mobile
            user.mobile_verified = False
        if image:
            user.profile_pic = image
        user.save()
        messages.success(request, "Profile updated.")
        return render(request, template_name)
    return render(request, template_name)

def send_sms_to_verify_mob_num(request):
    if User.objects.filter(mobile=request.user.mobile, mobile_verified=True).exclude(id=request.user.id).exists():
        return JsonResponse({'status': False, 'message':"Number Already Verfied with another account"})
    otp = generateNumber(4)
    request.user.mobile_verification_otp = otp
    request.user.save()
    return JsonResponse({'status': True, 'message':"OTP Send to your mobile number"})

def verify_mobile_number(request):
    if request.method == "POST":
        otp1 = request.POST.get('otp1')
        otp2 = request.POST.get('otp2')
        otp3 = request.POST.get('otp3')
        otp4 = request.POST.get('otp4')

        if not otp1 or not otp2 or not otp3 or not otp4:
            messages.error(request, "Please Enter OTP")
            return redirect('app_profile')

        otp = f'{otp1}{otp2}{otp3}{otp4}'

        user_obj = User.objects.filter(mobile=request.user.mobile, mobile_verified=False, id=request.user.id)
        if user_obj.exists():
            # otp bypass till client didn't give mobile sms api
            if otp == "1234":
                request.user.mobile_verified = 1
                request.user.mobile_verification_otp = None
                request.user.save()
                messages.success(request, "mobile number verified")
                return redirect('app_profile')
            
            if user_obj[0].mobile_verification_otp == otp:
                request.user.mobile_verified = 1
                request.user.mobile_verification_otp = None
                request.user.save()
                messages.success(request, "mobile number verified")
                return redirect('app_profile')
            else:
                messages.error(request, "OTP is wrong")
                return redirect('app_profile')
        else:
            request.user.mobile_verification_otp = None
            request.user.save()
            messages.error(request, "mobile number is already been verified")
            return redirect('app_profile')
    messages.error(request, "Only Accept POST request")
    return redirect('app_profile')


@role_required
def useraddress(request):
    user = request.user
    user_address = Address.objects.filter(user_id=user.id).order_by('-id')
    template_name = 'frontend/dashboard/my-address.html'
    if request.method == 'POST':
        data = request.POST
        title = request.POST.get('title')
        address = request.POST.get('address')
        area = request.POST.get('area')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        landmark = request.POST.get('landmark')
        phone_number = request.POST.get('phone_number')

        if title.isspace() or title == '':
            messages.error(request, "Name of address can't be blank.")
            return render(request, template_name, {'data':data, 'user_address':user_address, 'show_add_new_modal': True})
        if address.isspace() or address == '':
            messages.error(request, "Address can't be blank.")
            return render(request, template_name, {'data':data, 'user_address':user_address, 'show_add_new_modal': True})
        if area.isspace() or area == '':
            messages.error(request, "Area can't be blank.")
            return render(request, template_name, {'data':data, 'user_address':user_address, 'show_add_new_modal': True})
        if city.isspace() or city == '':
            messages.error(request, "City of address can't be blank.")
            return render(request, template_name, {'data':data, 'user_address':user_address, 'show_add_new_modal': True})
        if state.isspace() or state == '':
            messages.error(request, "State can't be blank.")
            return render(request, template_name, {'data':data, 'user_address':user_address, 'show_add_new_modal': True})
        if zip_code.isspace() or zip_code == '':
            messages.error(request, "Zip code can't be blank.")
            return render(request, template_name, {'data':data, 'user_address':user_address, 'show_add_new_modal': True})
        if landmark.isspace() or landmark == '':
            messages.error(request, "Landmark can't be blank.")
            return render(request, template_name, {'data':data, 'user_address':user_address, 'show_add_new_modal': True})
        if phone_number.isspace() or phone_number == '' or len(phone_number) != 10 or not phone_number.isnumeric():
            messages.error(request, "Mobile can't be blank or Must be 10 digit.")
            return render(request, template_name, {'data':data, 'user_address':user_address, 'show_add_new_modal': True})
        Address.objects.create(user_id=user.id, address_title=title, address=address, area=area, city=city, state=state, zipcode=zip_code, landmark=landmark, phone_number=phone_number)
        messages.success(request, "Address successfully created.")
        return redirect('app_address')
    return render(request, template_name, {'user_address':user_address, 'show_add_new_modal': False})

@role_required
def userEditaddress(request, slug):
    user = request.user
    edit_address = Address.objects.get(slug=slug)
    user_address = Address.objects.filter(user_id=user.id).order_by('-id')
    template_name = 'frontend/dashboard/my-address.html'
    if request.method == 'POST':
        data = request.POST
        title = request.POST.get('title')
        address = request.POST.get('address')
        area = request.POST.get('area')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        landmark = request.POST.get('landmark')
        phone_number = request.POST.get('phone_number')
        if title.isspace() or title == '':
            messages.error(request, "Name of address can't be blank.")
            return render(request, template_name, {'edit_address':data, 'user_address':user_address, 'show_edit_address_model': True, 'edit_address_slug': slug})
        if address.isspace() or address == '':
            messages.error(request, "Address can't be blank.")
            return render(request, template_name, {'edit_address':data, 'user_address':user_address, 'show_edit_address_model': True, 'edit_address_slug': slug})
        if area.isspace() or area == '':
            messages.error(request, "Area can't be blank.")
            return render(request, template_name, {'edit_address':data, 'user_address':user_address, 'show_edit_address_model': True, 'edit_address_slug': slug})
        if city.isspace() or city == '':
            messages.error(request, "City of address can't be blank.")
            return render(request, template_name, {'edit_address':data, 'user_address':user_address, 'show_edit_address_model': True, 'edit_address_slug': slug})
        if state.isspace() or state == '':
            messages.error(request, "State can't be blank.")
            return render(request, template_name, {'edit_address':data, 'user_address':user_address, 'show_edit_address_model': True, 'edit_address_slug': slug})
        if zip_code.isspace() or zip_code == '':
            messages.error(request, "Zip code can't be blank.")
            return render(request, template_name, {'edit_address':data, 'user_address':user_address, 'show_edit_address_model': True, 'edit_address_slug': slug})
        if landmark.isspace() or landmark == '':
            messages.error(request, "Landmark can't be blank.")
            return render(request, template_name, {'edit_address':data, 'user_address':user_address, 'show_edit_address_model': True, 'edit_address_slug': slug})
        if phone_number.isspace() or phone_number == '' or len(phone_number) != 10 or not phone_number.isnumeric():
            messages.error(request, "Mobile can't be blank or Must be 10 digit.")
            return render(request, template_name, {'edit_address':data, 'user_address':user_address, 'show_edit_address_model': True, 'edit_address_slug': slug})
        edit_address.address_title=title
        edit_address.address=address
        edit_address.area=area
        edit_address.city=city
        edit_address.state=state
        edit_address.zipcode=zip_code
        edit_address.landmark=landmark
        edit_address.phone_number=phone_number
        edit_address.save()
        messages.success(request, "Address successfully updated.")
        return redirect('app_address')
        # return render(request, template_name, {'user_address':user_address})
    return render(request, template_name, {'user_address':user_address, 'edit_address': edit_address, 'show_edit_address_model': True,  'edit_address_slug': slug})

@role_required
def userDeleteAddress(request, slug):
    address = Address.objects.get(slug=slug)
    address.delete()
    messages.success(request, "Address deleted!")
    return redirect('app_address')

@role_required
def usernotificationSetting(request):
    user = request.user
    template_name = 'frontend/dashboard/notification-setting.html'
    if request.method == 'POST':
        notification_settings = request.POST.get('settings')
        if notification_settings == '1':
            user.notification_settings = notification_settings
        else:
            user.notification_settings = 0
        user.save()
        return redirect('app_notification_sittings')
    return render(request, template_name)

def userInformation(request, slug):
    template_name = 'frontend/lender-box/user-information.html'
    user = User.objects.get(slug=slug)
    return render(request, template_name, {'user':user})

def userInformationRequestOTP(request, slug):
    template_name = 'frontend/lender-box/request-otp.html'
    user = UserProfileLenderBox.objects.get(slug=slug)
    if request.method == 'POST':
        sendOTPUserProfile(user)
        messages.success(request, "OTP send successfully. Please check email.")
        return redirect('verify_otp_profile', str(user.slug))
    return render(request, template_name, {'user':user})

def userInformationVerifyOTP(request, slug):
    template_name = 'frontend/lender-box/otp.html'
    user = UserProfileLenderBox.objects.get(slug=slug)
    if request.method == 'POST':
        otp1 = request.POST.get('otp1') 
        otp2 = request.POST.get('otp2') 
        otp3 = request.POST.get('otp3') 
        otp4 = request.POST.get('otp4')
        otp = otp1+otp2+otp3+otp4
        if otp1.isspace() or otp1 == '' and otp2.isspace() or otp2 == '' and otp3.isspace() or otp3 == '' and otp4.isspace() or otp4 == '':
            messages.error(request, "otp not be blank!")
            return redirect('verify_otp_profile', str(user.slug))
        if user.otp != int(otp):
            messages.error(request, "otp not matched!")
            return redirect('verify_otp_profile', str(user.slug))
        else:
            user.otp = 0
            user.save()
            messages.success(request, "OTP successfully verified.")
            return redirect('user_information', str(user.user.slug))
    return render(request, template_name, {'user':user})

def subscriptionListing(request):
    template_name = 'frontend/dashboard/subscription.html'
    subscriptions = SubscriptionPlan.objects.all().order_by('-id')
    is_user_have_subscription = UserSubscription.objects.filter(user_id=request.user.id).exists()
    return render(request, template_name, {'subscriptions':subscriptions, 'is_user_have_subscription': is_user_have_subscription})

def buySubscription(request, slug):
    try:
        user_data = request.user
        subscription_plans = SubscriptionPlan.objects.all()
        if not subscription_plans.filter(slug=slug).exists():
            messages.error(request, "Plan not found!")
            return redirect('subscription_listing')

        if not DwollaCustomer.objects.filter(user_id=user_data.id).exists():
            messages.error(request, "Wallet not found!")
            return redirect('subscription_listing')

        if UserSubscription.objects.filter(user_id=user_data.id).exists():
            messages.error(request, "You have already subscribed!")
            return redirect('subscription_listing')
        
        dwolla_wallet = LenderWallet.objects.get(user_id=user_data.id)
        admin_wallet = AdminAccount.objects.all()
        subscription_price = SubscriptionPlan.objects.get(slug=slug)
        if not check_wallet_amount(wallet_id=dwolla_wallet.wallet_id, amount=subscription_price.original_price):
            messages.error(request, "You have insufficient balance in your wallet.")
            return redirect('subscription_listing')
        try:
            transfer_data = {
                'amount': f'{subscription_price.original_price}',
                'funding_source': f'{dwolla_wallet.wallet_id}',
                'destination_source': f'{admin_wallet.first().wallet_id}',
                'message': f"Subscription plan purchase by {user_data.name}"
            }
            DwollaTransferAPI.create_transfer(transfer_data)
            plan_start_date = datetime.now().date() 
            plan_end_date = datetime.now().date() + timedelta(days=30)
            UserSubscription.objects.create(user_id=user_data.id, subscription_id=subscription_price.id, 
            amount=subscription_plans.get(slug=slug).original_price, status='ACTIVE', 
            plan=subscription_plans.get(slug=slug).name, current_period_end=plan_end_date, 
            current_period_start=plan_start_date)
            messages.success(request, "Subscription started successfully.")
            return redirect('subscription_listing')
        except TypeError as e:
            messages.error(request, e)
            return redirect('subscription_listing')
        except ValueError as e:
            messages.error(request, e)
            return redirect('subscription_listing')
        except Exception as e:
                messages.error(request, ' '.join(e))
                return redirect('subscription_listing')
    except:
        messages.error(request, "Something Went Wrong.")
        return redirect('subscription_listing')
