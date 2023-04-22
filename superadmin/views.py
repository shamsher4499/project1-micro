from api.bid_api.serializers import EMICalculationSerializer
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db.models import Max, Min, Sum, Count, Avg, Q, Prefetch
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.contrib.sessions.models import Session
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth.models import auth
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .tasks import loginAlertByCelery
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from datetime import datetime
from .generate_excel import generate_excel_file
from api.generate_pdf import generate_pdf
from api.dwolla_payment import DwollaCheckBalanceAPI, DwollaTransactionHistoryAPI
from django.urls import reverse
from .metrics import http_requests_total, http_request_duration_seconds, database_queries_total, database_query_duration_seconds

from .decorators import admin_only
from .models import *
from .utils import *
from .email import *

import jwt
import csv
import json
import stripe
import threading

@admin_only
def app_performance_tracker():
    http_requests_total.inc()
    # request2 = http_request_duration_seconds.
    # request3 = database_queries_total
    # request4 = database_query_duration_seconds
    return HttpResponse('Hello, World!')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def homepage(request):
    if not (request.user.is_authenticated and request.user.is_superuser):
        return redirect('admin_login')
    payload = {
        'id':3
    }
    token = jwt.encode(payload, 'secret', algorithm='HS256')
    payload = jwt.decode(token, 'secret', algorithms=['HS256'])
    template = 'admin/include/body.html'
    loans = BorrowerRequestAmount.objects.all()
    active_loans = loans.filter(approve=1, completed=0, reject=0).count()
    completed_loans = loans.filter(approve=1, completed=1).count()
    admin_amount = AdminEarning.objects.all()
    admin_amount_aggregate = admin_amount.aggregate(pending_amount = Sum('pending_amount'), received_amount = Sum('received_amount'))
    pending_amount = admin_amount_aggregate.get('pending_amount')
    received_amount = admin_amount_aggregate.get('received_amount')
    wallet = AdminAccount.objects.all().first()
    wallet_balance = DwollaCheckBalanceAPI.get_balance(wallet.wallet_id)
    all_user = User.objects.all()
    user = all_user.filter(is_superuser=False, is_store=False).count()
    store = all_user.filter(is_store=True).count()
    pending_user = all_user.filter(is_active=False, is_superuser=False).count()
    user_data= all_user.annotate(month=TruncMonth("created")).values("month").annotate(user_count=Count('pk', filter=Q(is_store=False, is_superuser=False)), 
                store_count=Count('pk', filter=Q(is_store=True)))
    month = {
        'January': {'user': 0,'store': 0},
		'February': {'user': 0,'store': 0},
		'March': {'user': 0,'store': 0},
		'April': {'user': 0,'store': 0},
		'May': {'user': 0,'store': 0},
		'June': {'user': 0,'store': 0},
		'July': {'user': 0,'store': 0},
		'August': {'user': 0,'store': 0},
		'September': {'user': 0,'store': 0},
		'October': {'user': 0,'store': 0},
		'November': {'user': 0,'store': 0},
		'December': {'user': 0,'store': 0}
        }
    for i in user_data:
        month[i.get('month').strftime("%B")] = {'user': i.get('user_count'), 'store': i.get('store_count')}
    context = {
        'user':user, 
        'store':store,
        'pending_user':pending_user,
        'month':month, 
        'wallet_balance':wallet_balance,
        'active_loans':active_loans,
        'completed_loans':completed_loans,
        'pending_amount':pending_amount,
        'received_amount':received_amount
        }
    return render(request, template, context)

def login(request):
    template = 'admin/auth/login.html'
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('homepage')
    elif request.method == 'POST':
        data = request.POST
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email.isspace() or email == '':
            messages.error(request, "Email can't be blank.")
            return render(request, template, {'data':data})
        elif password.isspace() or password == '':
            messages.error(request, "Password can't be blank.")
            return render(request, template, {'data':data})
        elif '@' not in email:
            messages.error(request, "Email Must be valid.")
            return render(request, template, {'data':data})
        admin = auth.authenticate(email=email,  password=password)
        if admin == None:
            messages.error(request, "Credentials not match.")
            return render(request, template, {'data':data})
        user_login = User.objects.get(email=email.lower())
        if not user_login.session_login:
            auth.login(request, admin)
            user_login.session_login = 1
            user_login.save()
            ip_address = get_ip()
            if ip_address:
                location = get_location(ip_address)
                loginAlert(email, location)
                # thread3 = threading.Thread(target=loginAlert, args=(email, location))
                # thread3.start()
            else:
                loginAlertByCelery(email, location)
            messages.success(request, "Login Success.")
            return redirect('homepage')
        session = Session.objects.all()
        for s in session:
            if s.get_decoded().get('_auth_user_id') != None:
                if s.get_decoded().get('_auth_user_id') == str(user_login.id):
                    s.delete()
        auth.login(request, admin)
        user_login.session_login = 1
        user_login.save()
        ip_address = get_ip()
        location = get_location(ip_address)
        loginAlert(email, location)
        # thread3 = threading.Thread(target=loginAlert, args=(email, location))
        # thread3.start()
        messages.success(request, "Login Success.")
        return redirect('homepage')
    return render(request, template)

def resendAdminOTP(slug):
    admin = User.objects.get(slug=slug, is_superuser=True)
    if admin.otp_sent_time != None:
        filter_date = str(admin.otp_sent_time)[:19]
        now_plus_10 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
        if datetime.now() >= now_plus_10:
            changePasswordOTP(admin)
            return {
                "status": True,
                "message": "Verification code sent on the mail address. Please check."
                }
        else:
            return {
                "status": False,
                "message": f"You can send next otp after 1 mintues. Please try after {str(now_plus_10)[11:]}."
                }
    else:
        changePasswordOTP(admin)
        return {
            "status": True,
            "message": "Verification code sent on the mail address. Please check."
            }

def forgetPasswordStep1(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('homepage')
    template = 'admin/auth/forgetPasswordStep1.html'
    if request.method == 'POST':
        data = request.POST
        email = request.POST.get('email')
        if email.isspace() or email == '':
            messages.error(request, "Email can't be blank.")
            return render(request, template, {'data':data})
        if '@' not in email:
            messages.error(request, "Email Must be valid.")
            return render(request, template, {'data':data})
        if User.objects.filter(email=email.lower(), is_superuser=True).exists():
            admin = User.objects.get(email=email.lower())
            if admin.otp_sent_time != None:
                filter_date = str(admin.otp_sent_time)[:19]
                now_plus_10 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
                if datetime.now() >= now_plus_10:
                    changePasswordOTP(admin)
                    messages.success(request, "OTP has been sent on email address. Please check Email Address.")
                    return redirect('admin_forget_password_step2', str(admin.slug))
                else:
                    messages.error(request, f"You can send next otp after 1 mintues. Please try after {str(now_plus_10)[11:]}.")
                    return render(request, template, {'data':data})
            else:
                changePasswordOTP(admin)
                messages.success(request, "OTP has been sent on email address. Please check Email Address.")
                return redirect('admin_forget_password_step2', str(admin.slug))
        messages.error(request, "Email not found!")
        return render(request, template, {'data':data})
    return render(request, template)

def forgetPasswordStep2(request, slug):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('homepage')
    template = 'admin/auth/forgetPasswordStep2.html'
    if request.method == 'POST':
        data = request.POST
        otp = request.POST.get('otp')
        if 'resend_otp' in request.POST:
            response = resendAdminOTP(slug)
            if response['status']:
                messages.success(request, response['message'])
            else:
                messages.info(request, response['message'])
            return redirect('admin_forget_password_step2', slug)
        if otp.isspace() or otp == '':
            messages.error(request, "OTP can't be blank.")
            return render(request, template, {'data':data})
        if not len(otp) == 4:
            messages.error(request, "OTP must be 4 digit.")
            return render(request, template, {'data':data})
        if len(otp) == 4 and not otp.isnumeric():
            messages.error(request, "OTP must be Numeric.")
            return render(request, template, {'data':data})
        if User.objects.filter(slug=slug, is_superuser=True).exists():
            admin = User.objects.get(slug=slug)
            if admin.otp == otp:
                admin.otp = None
                admin.save()
                messages.success(request, "Otp Successfully matched.")
                return redirect('admin_forget_password_step3', str(admin.slug), str(admin.slug_user))
            else:
                messages.error(request, "OTP not match.")
                return render(request, template, {'data':data})
        messages.error(request, "User not found!")
        return render(request, template, {'data':data})
    return render(request, template)

def forgetPasswordStep3(request, slug, user_slug):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('homepage')
    template = 'admin/auth/forgetPasswordStep3.html'
    if request.method == 'POST':
        data = request.POST
        newPassword = request.POST.get('newPassword')
        confirmPassword = request.POST.get('confirmPassword')
        if newPassword.isspace() or newPassword == '':
            messages.error(request, "New Password can't be blank.")
            return render(request, template, {'data':data})
        if confirmPassword.isspace() or confirmPassword == '':
            messages.error(request, "Confirm Password can't be blank.")
            return render(request, template, {'data':data})
        if not len(newPassword) > 7 or not len(newPassword) < 17:
            messages.error(request, "Password length must be between 8 to 16.")
            return render(request, template, {'data':data})
        if not len(confirmPassword) > 7 or not len(confirmPassword) < 17:
            messages.error(request, "Password length must be between 8 to 16.")
            return render(request, template, {'data':data})
        if newPassword != confirmPassword:
            messages.error(request, "New Password and Confirm Password not match.")
            return render(request, template, {'data':data})
        if User.objects.filter(slug=slug, is_superuser=True, slug_user=user_slug).exists():
            admin = User.objects.get(slug=slug)
            if not admin.check_password(confirmPassword):
                admin.set_password(confirmPassword)
                admin.save()
                ip_address = get_ip()
                location = get_location(ip_address)
                sendAlert(admin, location)
                messages.success(request, "Your Password has been changed.")
                return redirect('admin_login')
            else:
                messages.error(request, "You can't use old password!")
                return render(request, template, {'data':data})
        messages.error(request, "User not found!")
        return render(request, template, {'data':data})
    return render(request, template)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_only
def logout(request):
    user = request.user
    user.session_login = 0
    user.save()
    auth.logout(request)
    messages.success(request, "You have Successfully Logout")
    return redirect('admin_login')

@admin_only
def adminProfile(request):
    template = 'admin/auth/profile.html'
    if request.user.is_superuser == True:
        admin = User.objects.get(id=request.user.id)
    else:
        messages.error(request, "You are not a Superuser.")
        return redirect('admin_login')
    if request.method=="POST" and 'form1' in request.POST:
        data = request.POST
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        mobile = request.POST.get('mobile')
        if admin:
            if first_name.isspace() or first_name == '':
                messages.error(request, "First Name can't be blank.")
                return render(request, template, {'admin':admin})
            if last_name.isspace() or last_name == '':
                messages.error(request, "Last Name can't be blank.")
                return render(request, template, {'admin':admin})
            if mobile.isspace() or mobile == '' or len(mobile) != 10 or not mobile.isnumeric():
                messages.error(request, "Mobile can't be blank or Must be 10 digit.")
                return render(request, template, {'admin':admin})
            if User.objects.filter(mobile=mobile).exclude(id=request.user.id).exists():
                messages.error(request, "Mobile must be unique.")
                return render(request, template, {'admin':admin})
            admin.first_name=first_name
            admin.last_name=last_name
            admin.mobile=mobile
            admin.save()
            messages.success(request, "Successfully updated!")
            return redirect('admin_profile')
        else:
            messages.error(request, "Something went wrong!")
            return redirect('homepage')
    if request.method == 'POST' and 'form2' in request.POST:
        admin = User.objects.get(id=request.user.id)
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        if current_password.isspace() or current_password == '':
            messages.error(request, "Current Password can't be blank.")
            return render(request, template, {'admin':admin})
        if new_password.isspace() or new_password == '' or len(new_password) < 6:
            messages.error(request, "New Password can't be blank or Must be greater than 6 characters.")
            return render(request, template, {'admin':admin})
        if not admin.check_password(current_password):
            messages.error(request, "Current Password not matched!")
            return render(request, template, {'admin':admin})
        admin.set_password(new_password)
        admin.save()
        messages.success(request, 'Password Successfully Changed!')
        return render(request, template, {'admin':admin}) 
    return render(request, template, {'admin':admin})

#------------Borrowers CURD----------------------
# @check_user_type
@admin_only
def borrowersListing(request):
    template = 'admin/borrower-management/listing.html'
    if request.method == 'POST':
        data = request.POST
        search_user = User.objects.filter(is_store=False, is_superuser=False, is_active=True).filter(
            Q(name__contains=data['search_box'])|
            Q(email__contains=data['search_box'])|
            Q(mobile__contains=data['search_box']))
        p = Paginator(search_user, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = p.get_page(page_number) 
        except PageNotAnInteger:
            page_obj = p.page(1)
        except EmptyPage:
            page_obj = p.page(p.num_pages)
        context = {
            'page_obj':page_obj,
            'search_user':search_user,
            'search_count':search_user.count(),
            'search_object':data['search_box'],
            'search_record':True}
        return render(request, template, context)
    users = User.objects.filter(is_superuser=False, is_active=True, is_store=False).order_by('-id')
    p = Paginator(users, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'users':users, 'page_obj':page_obj})

@admin_only
def borrowersView(request, slug):
    template = 'admin/borrower-management/view.html'
    try:
        user = User.objects.get(slug=slug)
    except:
        user = None
    if user:
        total_loans = BorrowerRequestAmount.objects.all()
        lender = {'loans':0, 'amount':0, 'completed':0, 'rejected':0}
        borrower = {'loans':0, 'amount':0, 'completed':0, 'rejected':0}
        borrower['loans'] = total_loans.filter(user_id=user.id, approve=True, completed=False).count()
        borrower['completed'] = total_loans.filter(user_id=user.id, approve=True, completed=True).count()
        borrower['rejected'] = total_loans.filter(user_id=user.id, reject=True).count()
        borrower['amount'] = total_loans.filter(user_id=user.id, approve=True).aggregate(Sum('amount'))['amount__sum']

        lender['loans'] = total_loans.filter(lender_id=user.id, approve=True, completed=False).count()
        lender['completed'] = total_loans.filter(lender_id=user.id, approve=True, completed=True).count()
        lender['rejected'] = total_loans.filter(lender_id=user.id, reject=True).count()
        lender['amount'] = total_loans.filter(lender_id=user.id, approve=True).aggregate(Sum('amount'))['amount__sum']

        user_address = Address.objects.filter(user_id=user.id)
        user_wallet = LenderWallet.objects.filter(user_id=user.id).first()
        if user_wallet:
            wallet_balance = DwollaCheckBalanceAPI.get_balance(user_wallet.wallet_id)
        else: 
            wallet_balance = 0
        context = {'user':user, 'user_address':user_address, 'user_wallet':user_wallet, 'wallet_balance':wallet_balance,
                   'lender':lender,
                   'borrower':borrower}
        return render(request, template, context)
    else:
        messages.error(request, "User not found.")
        return redirect('borrower_listing')

@admin_only
def borrowersDelete(request, slug, slug_user):
    try:
        user = User.objects.get(Q(slug=slug) | Q(slug_user=slug))
    except:
        user = None
    if user:
        if user.customer_id:
            try:
                stripe.Customer.delete(user.customer_id)
                user.delete()
                accountReject(user)
                messages.success(request, "Deleted.")
                return redirect('borrower_listing')
            except:
                user.delete()
                accountReject(user)
                messages.success(request, "Deleted.")
                return redirect('borrower_listing')
        else:
            user.delete()
            accountReject(user)
            messages.success(request, "Deleted.")
            return redirect('borrower_listing')
    else:
        messages.error(request, "User not found.")
        return redirect('borrower_listing')


@admin_only
def borrowersAdd(request):
    template = 'admin/borrower-management/add.html'
    json_data = open("country_code.json")
    country_data = json.load(json_data)
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        select_code = request.POST.get('calling_code')
        email = request.POST.get('email')
        documents = request.FILES.get('documents')
        if not User.objects.filter(email=email.lower()).exists():
            if name.isspace() or name == '':
                messages.error(request, "Name can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if mobile.isspace() or mobile == '' or len(mobile) != 10 or not mobile.isnumeric():
                messages.error(request, "Mobile can't be blank or Must be 10 digit.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if User.objects.filter(mobile=mobile).exists():
                messages.error(request, "Mobile must be unique.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if email.isspace() or email == '' or '@' not in email:
                messages.error(request, "Email can't be blank or email must be valid.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if documents == None:
                messages.error(request, "Document must be .pdf format.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if not (documents.name.split('.')[-1]).lower() in docs_type:
                messages.error(request, "Document must be pdf,png,jpeg,xls only.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if not get_size(documents):
                messages.error(request, "Document size must be less than 5 MB.")
                return render(request, template, {'data':data, 'country_data':country_data})
            calling_code, country_code = select_code.split('$')[0], select_code.split('$')[1]
            user = User.objects.create(name=name, email=email.lower(), calling_code=calling_code, 
                country_code=country_code, mobile=mobile, document=documents, is_active=True, is_verified=True)
            customer_data = stripe.Customer.create(
                name=data['name'],
                email=data['email'].lower(),
                phone=data['mobile']
                )
            user.customer_id = customer_data['id']
            user.save_with_slug()
            sendCredentials(user)
            messages.success(request, "Successfully added!")
            return redirect('borrower_listing')
        else:
            messages.error(request, "Email or Mobile must be unique.")
            return render(request, template, {'data':data})
    return render(request, template, {'country_data':country_data})

@admin_only
def borrowersEdit(request, slug):
    json_data = open("country_code.json")
    country_data = json.load(json_data)
    template = 'admin/borrower-management/edit.html'
    try:
        user = User.objects.get(slug=slug)
    except:
        user = None
    if user:
        if request.method=="POST":
            name = request.POST.get('name')
            mobile = request.POST.get('mobile')
            select_code = request.POST.get('calling_code')
            status = request.POST.get('status')
            documents = request.FILES.get('documents')
            if name.isspace() or name == '':
                messages.error(request, "Name can't be blank.")
                return render(request, template, {'user':user})
            if mobile.isspace() or mobile == '' or len(mobile) != 10 or not mobile.isnumeric():
                messages.error(request, "Mobile can't be blank or Must be 10 digit and Unique.")
                return render(request, template, {'user':user})
            if User.objects.filter(mobile=mobile).exclude(slug=slug).exists():
                messages.error(request, "Mobile Must be Unique.")
                return render(request, template, {'user':user}) 
            if documents:
                if not (documents.name.split('.')[-1]).lower() in docs_type:
                    messages.error(request, "Document must be pdf,png,jpeg,xls only.")
                    return render(request, template, {'user':user})
                if not get_size(documents):
                    messages.error(request, "Document size must be less than 5 MB.")
                    return render(request, template, {'user':user})
            if not documents:
                documents = user.document
            user.name = name
            user.calling_code, user.country_code = select_code.split('$')[0], select_code.split('$')[1]
            user.document = documents
            user.mobile = mobile
            user.is_active = status
            user.save()
            messages.success(request, "Successfully updated!")
            return redirect('borrower_listing')
        return render(request, template, {'user':user, 'country_data':country_data})
    else:
        messages.error(request, "User not found.")
        return redirect('borrower_listing')

#-------------------End Borrower CURD-------------------


#------------Store CURD----------------------
@admin_only
def storeListing(request):
    template = 'admin/store-management/listing.html'
    if request.method == 'POST':
        data = request.POST
        search_user = StoreProfile.objects.filter(user__is_store=True, user__is_superuser=False, user__is_active=True).filter(
            Q(store_name__contains=data['search_box'])|
            Q(user__email__contains=data['search_box'])|
            Q(user__mobile__contains=data['search_box']))
        p = Paginator(search_user, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = p.get_page(page_number) 
        except PageNotAnInteger:
            page_obj = p.page(1)
        except EmptyPage:
            page_obj = p.page(p.num_pages)
        context = {
            'page_obj':page_obj,
            'search_user':search_user,
            'search_count':search_user.count(),
            'search_object':data['search_box'],
            'search_record':True}
        return render(request, template, context)
    store = StoreProfile.objects.filter(user__is_active=True, user__is_store=True).order_by('-id')
    p = Paginator(store, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'store':store, 'page_obj':page_obj})

@admin_only
def storeView(request, slug):
    template = 'admin/store-management/view.html'
    try:
        user = User.objects.get(slug=slug)
    except:
        user = None
    if user:
        store = StoreProfile.objects.get(user_id=user.id)
        total_loans = StoreLoanEmi.objects.all()
        borrower = {'loans':0, 'amount':0, 'completed':0, 'rejected':0}
        borrower['loans'] = total_loans.filter(store_id=user.id, approve=True, completed=False).count()
        borrower['completed'] = total_loans.filter(store_id=user.id, approve=True, completed=True).count()
        borrower['rejected'] = total_loans.filter(store_id=user.id, reject=True).count()
        borrower['amount'] = total_loans.filter(store_id=user.id, approve=True).aggregate(Sum('amount'))['amount__sum']

        store_wallet = LenderWallet.objects.filter(user_id=user.id).first()
        if store_wallet:
            wallet_balance = DwollaCheckBalanceAPI.get_balance(store_wallet.wallet_id)
        else: 
            wallet_balance = 0
        context = {'store':store, 'store_wallet':store_wallet, 'wallet_balance':wallet_balance,
                    'borrower':borrower}
        return render(request, template, context)
    else:
        messages.error(request, "User not found.")
        return redirect('borrower_listing')


@admin_only
def storeDelete(request, slug, slug_user):
    try:
        user = User.objects.get(Q(slug=slug) | Q(slug_user=slug))
    except:
        user = None
    if user:
        if user.customer_id:
            try:
                stripe.Customer.delete(user.customer_id)
                user.delete()
                accountReject(user)
                messages.success(request, "Deleted.")
                return redirect('store_listing')
            except:
                user.delete()
                accountReject(user)
                messages.success(request, "Deleted.")
                return redirect('store_listing')
        else:
            user.delete()
            accountReject(user)
            messages.success(request, "Deleted.")
            return redirect('store_listing')
    else:
        messages.error(request, "Store not found.")
        return redirect('store_listing')

@admin_only
def storeAdd(request):
    template = 'admin/store-management/add.html'
    json_data = open("country_code.json")
    country_data = json.load(json_data)
    if request.method=="POST":
        data = request.POST
        store_name = request.POST.get('store_name')
        mobile = request.POST.get('mobile')
        select_code = request.POST.get('calling_code')
        email = request.POST.get('email')
        address = request.POST.get('address')
        name = request.POST.get('name')
        dob = request.POST.get('dob')
        tax_id = request.POST.get('tax_id')
        store_open_time = request.POST.get('store_open_time')
        store_close_time = request.POST.get('store_close_time')
        store_open_day = request.POST.get('store_open_day')
        business_type = request.POST.get('business_type')
        documents = request.FILES.get('documents')
        profile_pic = request.FILES.get('profile_pic')
        if not User.objects.filter(email=email.lower()).exists():
            if store_name.isspace() or store_name == '':
                messages.error(request, "Store Name can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if mobile.isspace() or mobile == '' or len(mobile) != 10 or not mobile.isnumeric():
                messages.error(request, "Mobile can't be blank or Must be 10 digit.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if User.objects.filter(mobile=mobile).exists():
                messages.error(request, "Mobile must be unique.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if email.isspace() or email == '' or '@' not in email:
                messages.error(request, "Email can't be blank or email must be valid.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if address.isspace() or address == '':
                messages.error(request, "Address can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if name.isspace() or name == '':
                messages.error(request, "Owner name can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if dob.isspace() or dob == '':
                messages.error(request, "Birth of date can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if tax_id.isspace() or tax_id == '':
                messages.error(request, "Tax Id can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if StoreProfile.objects.filter(tax_id=tax_id).exists():
                messages.error(request, "Tax Id must be unique.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if store_open_time.isspace() or store_open_time == '':
                messages.error(request, "Store open time can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if store_close_time.isspace() or store_close_time == '':
                messages.error(request, "Store close time can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if store_open_day.isspace() or store_open_day == '':
                messages.error(request, "Store open day can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if business_type.isspace() or business_type == '':
                messages.error(request, "Business type can't be blank.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if documents == None:
                messages.error(request, "Document must be .pdf format.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if not (documents.name.split('.')[-1]).lower() in docs_type:
                messages.error(request, "Document must be pdf,png,jpeg,xls only.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if not get_size(documents):
                messages.error(request, "Document size must be less than 5 MB.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if profile_pic == None:
                messages.error(request, "Image must be .jpg format.")
                return render(request, template, {'data':data, 'country_data':country_data})
            if not (profile_pic.name.split('.')[-1]).lower() in docs_type:
                messages.error(request, "Image must be png, jpeg, jpg only.")
                return render(request, template, {'data':data, 'country_data':country_data})
            calling_code, country_code = select_code.split('$')[0], select_code.split('$')[1]
            user = User.objects.create(name=name, email=email.lower(), calling_code=calling_code, 
                country_code=country_code, mobile=mobile, profile_pic=profile_pic if profile_pic else None, document=documents, is_active=True, is_verified=True, is_store=True)
            StoreProfile.objects.create(user_id=user.id, store_close_time=store_close_time, store_open_day=store_open_day, store_open_time=store_open_time,
            tax_id=tax_id, store_name=store_name, business_type=business_type, dob=dob, address=address)
            customer_data = stripe.Customer.create(
                name=data['store_name'],
                email=data['email'].lower(),
                phone=data['mobile']
                )
            user.customer_id = customer_data['id']
            user.save_with_slug()
            sendCredentials(user)
            messages.success(request, "Successfully added!")
            return redirect('store_listing')
        else:
            messages.error(request, "Email or Mobile must be unique.")
            return render(request, template, {'data':data})
    return render(request, template, {'country_data':country_data})

@admin_only
def storeEdit(request, slug):
    template = 'admin/store-management/edit.html'
    json_data = open("country_code.json")
    country_data = json.load(json_data)
    try:
        store = StoreProfile.objects.get(user__slug=slug)
    except:
        store = None
    if store:
        if request.method=="POST":
            data = request.POST
            store_name = request.POST.get('store_name')
            mobile = request.POST.get('mobile')
            select_code = request.POST.get('calling_code')
            address = request.POST.get('address')
            name = request.POST.get('name')
            dob = request.POST.get('dob')
            tax_id = request.POST.get('tax_id')
            store_open_time = request.POST.get('store_open_time')
            store_close_time = request.POST.get('store_close_time')
            store_open_day = request.POST.get('store_open_day')
            business_type = request.POST.get('business_type')
            documents = request.FILES.get('documents')
            profile_pic = request.FILES.get('profile_pic')
            if store_name.isspace() or store_name == '':
                messages.error(request, "Store Name can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if mobile.isspace() or mobile == '' or len(mobile) != 10 or not mobile.isnumeric():
                messages.error(request, "Mobile can't be blank or Must be 10 digit.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if User.objects.filter(mobile=mobile).exclude(slug=slug).exists():
                messages.error(request, "Mobile must be unique.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if address.isspace() or address == '':
                messages.error(request, "Address can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if name.isspace() or name == '':
                messages.error(request, "Owner name can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if dob.isspace() or dob == '':
                messages.error(request, "Birth of date can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if tax_id.isspace() or tax_id == '':
                messages.error(request, "Tax Id can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if StoreProfile.objects.filter(tax_id=tax_id).exclude(user__slug=slug).exists():
                messages.error(request, "Tax Id must be unique.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if store_open_time.isspace() or store_open_time == '':
                messages.error(request, "Store open time can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if store_close_time.isspace() or store_close_time == '':
                messages.error(request, "Store close time can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if store_open_day.isspace() or store_open_day == '':
                messages.error(request, "Store open day can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if business_type.isspace() or business_type == '':
                messages.error(request, "Business type can't be blank.")
                return render(request, template, {'store':store, 'country_data':country_data})
            if documents:
                if not (documents.name.split('.')[-1]).lower() in docs_type:
                    messages.error(request, "Document must be pdf,png,jpeg,xls only.")
                    return render(request, template, {'store':store})
                if not get_size(documents):
                    messages.error(request, "Document size must be less than 5 MB.")
                    return render(request, template, {'store':store})
            if profile_pic:
                if not (profile_pic.name.split('.')[-1]).lower() in docs_type:
                    messages.error(request, "Image must be png, jpeg, jpg only.")
                    return render(request, template, {'store':store, 'country_data':country_data})
                if not get_size(profile_pic):
                    messages.error(request, "Image size must be less than 5 MB.")
                    return render(request, template, {'store':store})
            calling_code, country_code = select_code.split('$')[0], select_code.split('$')[1]
            if not documents:
                documents = store.user.document
            if not profile_pic:
                profile_pic = store.user.profile_pic
            store.address = address
            store.store_open_time = store_open_time
            store.store_close_time = store_close_time
            store.store_open_day = store_open_day
            store.store_name = store_name
            store.tax_id = tax_id
            store.dob = dob
            store.business_type = business_type
            store.user.calling_code = calling_code
            store.user.country_code = country_code
            store.user.mobile = mobile
            store.user.document = documents
            store.user.profile_pic = profile_pic
            store.save()
            messages.success(request, "Successfully updated!")
            return redirect('store_listing')
        return render(request, template, {'country_data':country_data, 'store':store})
    else:
        messages.error(request, "Store not found.")
        return redirect('store_listing')

#-------------------End Store CURD-------------------



#---------------Team CURD--------------------
@admin_only
def teamListing(request):
    template = 'admin/testimonial-management/listing.html'
    testimonial = Testimonial.objects.all().order_by('-id')
    p = Paginator(testimonial, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'testimonial':testimonial, 'page_obj':page_obj})

@admin_only
def teamView(request, slug):
    template = 'admin/testimonial-management/view.html'
    testimonial = Testimonial.objects.get(slug=slug)
    return render(request, template, {'testimonial':testimonial})

@admin_only
def teamDelete(request, slug):
    try:
        testimonial = Testimonial.objects.get(slug=slug)
    except:
        testimonial = None
    if testimonial:
        testimonial.delete()
        messages.success(request, "Deleted.")
        return redirect('testimonial_listing')
    else:
        messages.error(request, "Testimonial not found.")
        return redirect('testimonial_listing')

@admin_only
def teamAdd(request):
    template = 'admin/testimonial-management/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        position = request.POST.get('position')
        desc = request.POST.get('desc')
        image = request.FILES.get('image')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'data':data})
        if position.isspace() or position == '':
            messages.error(request, "Position can't be blank.")
            return render(request, template, {'data':data})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'data':data})
        if image == None:
            messages.error(request, "Image must be .png, .jpeg format.")
            return render(request, template, {'data':data})
        if image.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
                messages.error(request, "Image must be .jpg, .jpeg, .png format.")
                return render(request, template, {'data':data})
        testimonial = Testimonial.objects.create(name=name, position=position, desc=desc, image=image, is_active=True)
        testimonial.save()
        messages.success(request, "Successfully Added!")
        return redirect('testimonial_listing')
    return render(request, template)

@admin_only
def teamEdit(request, slug):
    template = 'admin/testimonial-management/edit.html'
    testimonial_data = Testimonial.objects.get(slug=slug)
    if request.method=="POST":
        name = request.POST.get('name')
        position = request.POST.get('position')
        desc = request.POST.get('desc')
        image = request.FILES.get('image')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'testimonial_data':testimonial_data})
        if position.isspace() or position == '':
            messages.error(request, "Position can't be blank.")
            return render(request, template, {'testimonial_data':testimonial_data})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'testimonial_data':testimonial_data})
        if image and image.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'testimonial_data':testimonial_data})
        testimonial_data.name = name
        testimonial_data.position = position
        testimonial_data.desc = desc
        if image:
            testimonial_data.image = image
        testimonial_data.save()
        messages.success(request, "Successfully updated!")
        return redirect('testimonial_listing')
    return render(request, template, {'testimonial_data':testimonial_data})

#--------------- Social Account --------------------
@admin_only
def socialEdit(request):
    
    template = 'admin/social-management/edit.html'
    try:
        social_data = SocialAccount.objects.get(id=1)
    except:
        social_data = None
    # social_data = get_object_or_404(SocialAccount, id=1)
    if request.method=="POST":
        facebook = request.POST.get('facebook')
        instagram = request.POST.get('instagram')
        youtube = request.POST.get('youtube')
        linkedin = request.POST.get('linkedin')
        twitter = request.POST.get('twitter')
        if facebook.isspace() or 'https://' not in facebook:
            messages.error(request, "Please Enter Valid Url.")
            return render(request, template, {'social_data':social_data})
        if instagram.isspace() or 'https://' not in instagram:
            messages.error(request, "Please Enter Valid Url.")
            return render(request, template, {'social_data':social_data})
        if youtube.isspace() or 'https://' not in youtube:
            messages.error(request, "Please Enter Valid Url.")
            return render(request, template, {'social_data':social_data})
        if linkedin.isspace() or 'https://' not in linkedin:
            messages.error(request, "Please Enter Valid Url.")
            return render(request, template, {'social_data':social_data})
        if twitter.isspace() or 'https://' not in twitter:
            messages.error(request, "Please Enter Valid Url.")
            return render(request, template, {'social_data':social_data})
        social_data.facebook = facebook
        social_data.instagram = instagram
        social_data.youtube = youtube
        social_data.twitter = twitter
        social_data.linkedin = linkedin
        social_data.save()
        messages.success(request, "Successfully updated!")
        return redirect('edit_social')
    return render(request, template, {'social_data':social_data})

#--------------- HomePage Youtube Video --------------------
@admin_only
def youtubeEdit(request):
    template = 'admin/youtube/edit.html'
    try:
        youtube_id = YoutubeVideoID.objects.get(id=1)
    except:
        youtube_id = None
    if request.method=="POST":
        youtube = request.POST.get('youtube')
        thumbnail = request.FILES.get('thumbnail')
        if youtube.isspace() or youtube == '':
            messages.error(request, "Please Enter Valid youtube ID.")
            return render(request, template, {'youtube_id':youtube_id})
        if thumbnail and thumbnail.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'youtube_id':youtube_id})
        if thumbnail:
            youtube_id.thumbnail = thumbnail
        youtube_id.youtube_id = youtube
        youtube_id.save()
        messages.success(request, "Successfully updated!")
        return redirect('edit_youtube_id')
    return render(request, template, {'youtube_id':youtube_id})


#--------------- HomePage CURD --------------------
@admin_only
def homepageEdit(request):
    template = 'admin/homepage-management/edit.html'
    try:
        homepage = WebHomePage.objects.get(id=1)
    except:
        homepage = None
    if request.method=="POST":
        name = request.POST.get('name')
        name2 = request.POST.get('name2')
        name3 = request.POST.get('name3')
        name4 = request.POST.get('name4')
        name5 = request.POST.get('name5')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        image4 = request.FILES.get('image4')
        image5 = request.FILES.get('image5')
        desc1 = request.POST.get('desc1')
        desc2 = request.POST.get('desc2')
        desc3 = request.POST.get('desc3')
        desc4 = request.POST.get('desc4')
        desc5 = request.POST.get('desc5')
        if name.isspace() or name == '':
            messages.error(request, "Please Enter Valid name.")
            return render(request, template, {'homepage':homepage})
        if name2.isspace() or name2 == '':
            messages.error(request, "Please Enter Valid name.")
            return render(request, template, {'homepage':homepage})
        if name3.isspace() or name3 == '':
            messages.error(request, "Please Enter Valid name.")
            return render(request, template, {'homepage':homepage})
        if name4.isspace() or name4 == '':
            messages.error(request, "Please Enter Valid name.")
            return render(request, template, {'homepage':homepage})
        if name5.isspace() or name5 == '':
            messages.error(request, "Please Enter Valid name.")
            return render(request, template, {'homepage':homepage})
        if image1 and image1.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'homepage':homepage})
        if image2 and image2.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'homepage':homepage})
        if image3 and image3.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'homepage':homepage})
        if image4 and image4.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'homepage':homepage})
        if image5 and image5.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'homepage':homepage})
        if desc1.isspace() or desc1 == '':
            messages.error(request, "Please Enter Valid description.")
            return render(request, template, {'homepage':homepage})
        if desc2.isspace() or desc2 == '':
            messages.error(request, "Please Enter Valid description.")
            return render(request, template, {'homepage':homepage})
        if desc3.isspace() or desc3 == '':
            messages.error(request, "Please Enter Valid description.")
            return render(request, template, {'homepage':homepage})
        if desc4.isspace() or desc4 == '':
            messages.error(request, "Please Enter Valid description.")
            return render(request, template, {'homepage':homepage})
        if desc5.isspace() or desc5 == '':
            messages.error(request, "Please Enter Valid description.")
            return render(request, template, {'homepage':homepage})
        if image1:
            homepage.image1 = image1
        if image2:
            homepage.image2 = image2
        if image3:
            homepage.image3 = image3
        if image4:
            homepage.image4 = image4
        if image5:
            homepage.image5 = image5
        homepage.name = name
        homepage.name2 = name2
        homepage.name3 = name3
        homepage.name4 = name4
        homepage.name5 = name5
        homepage.desc1 = desc1
        homepage.desc2 = desc2
        homepage.desc3 = desc3
        homepage.desc4 = desc4
        homepage.desc5 = desc5
        homepage.save()
        messages.success(request, "Successfully updated!")
        return redirect('edit_homepage_id')
    return render(request, template, {'homepage':homepage})

#---------------Email Template CURD--------------------
@admin_only
def emailListing(request):   
    template = 'admin/email-management/listing.html'
    email_template = EmailTemplate.objects.all().order_by('-id')
    p = Paginator(email_template, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'email_template':email_template, 'page_obj':page_obj})

@admin_only
def emailView(request, slug): 
    template = 'admin/email-management/view.html'
    email_template = EmailTemplate.objects.get(slug=slug)
    return render(request, template, {'email_template':email_template})

@admin_only
def emailDelete(request, slug):
    try:
        email_template = EmailTemplate.objects.get(slug=slug)
    except:
        email_template = None
    if email_template:
        email_template.delete()
        messages.success(request, "Deleted.")
        return redirect('email_listing')
    else:
        messages.error(request, "Email Template not found.")
        return redirect('email_listing')

@admin_only
def emailAdd(request): 
    template = 'admin/email-management/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        if name.isspace() or name == '':
            messages.error(request, "Title can't be blank.")
            return render(request, template, {'data':data})
        if desc.isspace() or desc == '':
            messages.error(request, "Email Content can't be blank.")
            return render(request, template, {'data':data})
        email_template = EmailTemplate.objects.create(name=name, editor=desc, is_active=True)
        email_template.save()
        messages.success(request, "Successfully Added!")
        return redirect('email_listing')
    return render(request, template)

@admin_only
def emailEdit(request, slug):   
    template = 'admin/email-management/edit.html'
    email_template = EmailTemplate.objects.get(slug=slug)
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        desc = request.POST.get('editor')
        if name.isspace() or name == '':
            messages.error(request, "Title can't be blank.")
            return render(request, template, {'email_template':email_template})
        if desc.isspace() or desc == '':
            messages.error(request, "Email Content can't be blank.")
            return render(request, template, {'email_template':email_template})
        email_template.name = name
        email_template.editor = desc
        email_template.save()
        messages.success(request, "Successfully updated!")
        return redirect('email_listing')
    return render(request, template, {'email_template':email_template})
#---------------------------end--------------------------

#----------------------CURD Inquiry-----------------------
@admin_only
def inquiryListing(request):
    template = 'admin/inquiry-management/listing.html'
    inquiry = ContactUs.objects.filter(status='PENDING').order_by('-id')
    p = Paginator(inquiry, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'inquiry':inquiry, 'page_obj':page_obj})

@admin_only
def inquiryResolvedListing(request):
    template = 'admin/inquiry-management/resolved.html'
    inquiry = ContactUs.objects.filter(status='RESOLVED').order_by('-id')
    p = Paginator(inquiry, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'inquiry':inquiry, 'page_obj':page_obj})

@admin_only
def replyInquiry(request, slug):
    try:
        template = 'admin/inquiry-management/reply.html'
        inquiry = get_object_or_404(ContactUs, slug=slug)
        if inquiry:
            if request.method == 'POST':
                data = request.POST
                answer = request.POST.get('answer')
                if answer == '' or answer.isspace():
                    messages.error(request, "Answer can't be blank.")
                    return render(request, template, {'inquiry':inquiry})
                inquiry.answer = answer
                inquiry.status = 'RESOLVED'
                inquiry.reply_date = datetime.now()
                inquiry.save()
                sendInquiryReply(inquiry)
                return redirect('inquiry_listing')
        return render(request, template, {'inquiry':inquiry})
    except:
        return render(request, template, {'inquiry':inquiry})

@admin_only 
def resolvedDelete(request, slug):
    contact = get_object_or_404(ContactUs, slug=slug)
    if contact:
        contact.delete()
        messages.success(request, "Deleted")
        return redirect('inquiry_resolved')
    return redirect('inquiry_resolved')

#-----------------------Report Management----------------------

@admin_only
def user_report_list(request):
    template = 'admin/report-management/borrower.html'
    if request.method == 'POST':
        # user_wallet = LenderWallet.objects.all().values('user_id', 'amount')
        user = User.objects.filter(is_store=False, is_superuser=False).order_by('-id').values('name', 'email', 'mobile', 'is_active', 'is_verified', 'created')
        headers_list = ['Sr.', 'Name', 'Email', 'Mobile Number', 'Status', 'Email Verified', 'Date of joined']
        user_data = []
        for i,j in enumerate(user):
            user_data.append({
                'Sr.': i+1,
                'Name':j['name'],
                'Email':j['email'],
                'Mobile Number':j['mobile'],
                'Status': 'Active' if j['is_active'] else 'Inactive',
                'Email Verified':'Verified' if j['is_verified'] else 'Unverified',
                # 'Wallet': user_wallet['amount'] if j['id'] in user_wallet['user_id'] else 0,
                'Date of joined':j['created'].date()
            })
        file_name = datetime.now()
        data = generate_excel_file(f'media/reports/users/{file_name}.xlsx', 'All Users', headers_list, user_data)
        if data == None:
            messages.success(request, 'Excel file successfully generated.')
            return redirect(f'/media/reports/users/{file_name}.xlsx')
        else:
            messages.error(request, 'Error occurred.')
            return render(request, template)
    return render(request, template)

@admin_only
def borrowerGenerateReport(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="somefilename.csv"'},
    )
    writer = csv.writer(response)
    writer.writerow(['First Name', 'Last Name', 'Email Address', 'Mobile Number', 'User Type'])
    borrower = User.objects.filter(user_type='BORROWER').order_by('-id')
    for i in borrower:
        writer.writerow([i.first_name, i.last_name, i.email, i.mobile, i.user_type])
    return response

#-------------------------end----------------------

#--------------------pending users-----------------------
@admin_only
def pendingUsersListing(request): 
    template = 'admin/pending-users/listing.html'
    users = User.objects.filter(is_active=False, is_superuser=False).order_by('-id')
    p = Paginator(users, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'users':users, 'page_obj':page_obj})

@admin_only
def pendingUsersView(request, slug):
    template = 'admin/pending-users/view.html'
    user = User.objects.get(slug=slug)
    return render(request, template, {'user':user})

@admin_only
def verifyPendingUsersView(request, slug):
    user = User.objects.get(slug=slug)
    user.is_active = True
    user.save()
    sendApproveMail(user)
    messages.success(request, "Status changed successfully.")
    return redirect('pending_users')

@admin_only
def pendingUserDelete(request, slug):
    try:
        user = User.objects.get(Q(slug=slug))
    except:
        user = None
    if user:
        if user.customer_id:
            try:
                stripe.Customer.delete(user.customer_id)
                user.delete()
                accountReject(user)
                messages.success(request, "Deleted.")
                return redirect('pending_users')
            except:
                user.delete()
                accountReject(user)
                messages.success(request, "Deleted.")
                return redirect('pending_users')
        else:
            user.delete()
            accountReject(user)
            messages.success(request, "Deleted.")
            return redirect('pending_users')
    else:
        messages.error(request, "User not found.")
        return redirect('pending_users')

#---------------Blog CURD--------------------
@admin_only
def blogListing(request):
    template = 'admin/blog-management/listing.html'
    blog = Blog.objects.all().order_by('-id')
    p = Paginator(blog, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'blog':blog, 'page_obj':page_obj})

@admin_only
def blogView(request, slug, blog_slug):
    template = 'admin/blog-management/view.html'
    blog = Blog.objects.get(slug=slug)
    return render(request, template, {'blog':blog})

@admin_only
def blogDelete(request, slug):
    try:
        blog = Blog.objects.get(slug=slug)
    except:
        blog = None
    if blog:
        blog.delete()
        messages.success(request, "Deleted.")
        return redirect('blog_listing')
    else:
        messages.error(request, "Blog not found.")
        return redirect('blog_listing')

@admin_only
def blogAdd(request): 
    template = 'admin/blog-management/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        image = request.FILES.get('image')
        if not Blog.objects.filter(blog_slug=name.lower().replace(" ",'-')).exists():
            if name.isspace() or name == '':
                messages.error(request, "Name can't be blank.")
                return render(request, template, {'data':data})
            if desc.isspace() or desc == '':
                messages.error(request, "Description can't be blank.")
                return render(request, template, {'data':data})
            if image == None:
                messages.error(request, "Image must be .png, .jpeg format.")
                return render(request, template, {'data':data})
            if image.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
                messages.error(request, "Image must be .jpg, .jpeg, .png format.")
                return render(request, template, {'data':data})
            blog = Blog.objects.create(name=name, desc=desc, image=image, is_active=True)
            blog.save()
            messages.success(request, "Successfully Added!")
            return redirect('blog_listing')
        else:
            messages.error(request, "Name must be unique!")
            return render(request, template, {'data':data})
    return render(request, template)

@admin_only
def blogEdit(request, slug, blog_slug):
    template = 'admin/blog-management/edit.html'
    blog = Blog.objects.get(slug=slug)
    if request.method=="POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        image = request.FILES.get('image')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'blog':blog})
        if Blog.objects.filter(blog_slug=name.lower().replace(" ",'-')).exists():
            messages.error(request, "Name must be unique.")
            return render(request, template, {'blog':blog})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'blog':blog})
        if image and image.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'blog':blog})
        blog.name = name
        blog.desc = desc
        if image:
            blog.image = image
        blog.save()
        messages.success(request, "Successfully updated!")
        return redirect('blog_listing')
    return render(request, template, {'blog':blog})

#---------------About-us CURD--------------------
@admin_only
def aboutUsListing(request):
    template = 'admin/aboutus-management/listing.html'
    about = AboutUs.objects.all().order_by('-id')
    p = Paginator(about, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'about':about, 'page_obj':page_obj})

@admin_only
def aboutUsView(request, slug):
    template = 'admin/aboutus-management/view.html'
    blog = Blog.objects.get(slug=slug)
    return render(request, template, {'blog':blog})

@admin_only
def aboutUsDelete(request, slug):
    try:
        blog = Blog.objects.get(slug=slug)
    except:
        blog = None
    if blog:
        blog.delete()
        messages.success(request, "Deleted.")
        return redirect('blog_listing')
    else:
        messages.error(request, "Blog not found.")
        return redirect('blog_listing')

@admin_only
def aboutUsAdd(request): 
    template = 'admin/aboutus-management/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        image = request.FILES.get('image')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'data':data})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'data':data})
        if image == None:
            messages.error(request, "Image must be .png, .jpeg format.")
            return render(request, template, {'data':data})
        if image.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
                messages.error(request, "Image must be .jpg, .jpeg, .png format.")
                return render(request, template, {'data':data})
        blog = Blog.objects.create(name=name, desc=desc, image=image, is_active=True)
        blog.save()
        messages.success(request, "Successfully Added!")
        return redirect('blog_listing')
    return render(request, template)

@admin_only
def aboutUsEdit(request, slug):
    template = 'admin/aboutus-management/edit.html'
    about_us = AboutUs.objects.get(slug=slug)
    if request.method=="POST":
        name = request.POST.get('name')
        desc1 = request.POST.get('desc-top')
        desc2 = request.POST.get('desc-left')
        desc3 = request.POST.get('desc-right')
        image1 = request.FILES.get('image-top')
        image2= request.FILES.get('image-left')
        image3 = request.FILES.get('image-right')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'about_us':about_us})
        if desc1.isspace() or desc1 == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'about_us':about_us})
        if desc2.isspace() or desc2 == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'about_us':about_us})
        if desc3.isspace() or desc3 == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'about_us':about_us})
        if image1 and image1.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'about_us':about_us})
        if image2 and image2.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'about_us':about_us})
        if image3 and image3.name.split('.')[-1] not in ['jpg', 'png', 'jpeg']:
            messages.error(request, "Image must be .jpg, .jpeg, .png format.")
            return render(request, template, {'about_us':about_us})
        about_us.name = name
        about_us.desc1 = desc1
        about_us.desc2 = desc2
        about_us.desc3 = desc3
        if image1:
            about_us.image1 = image1
        if image2:
            about_us.image2 = image2
        if image3:
            about_us.image3 = image3
        about_us.save()
        messages.success(request, "Successfully updated!")
        return redirect('about_listing')
    return render(request, template, {'about_us':about_us})


#---------------FAQ CURD--------------------
@admin_only
def faqListing(request):
    template = 'admin/faq-management/listing.html'
    faq = FAQ.objects.all().order_by('-id')
    p = Paginator(faq, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'faq':faq, 'page_obj':page_obj})

@admin_only
def faqView(request, slug):
    template = 'admin/faq-management/view.html'
    faq = FAQ.objects.get(slug=slug)
    return render(request, template, {'faq':faq})

@admin_only
def faqDelete(request, slug):
    try:
        faq = FAQ.objects.get(slug=slug)
    except:
        faq = None
    if faq:
        faq.delete()
        messages.success(request, "Deleted.")
        return redirect('faq_listing')
    else:
        messages.error(request, "FAQ not found.")
        return redirect('faq_listing')

@admin_only
def faqAdd(request): 
    template = 'admin/faq-management/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        if name.isspace() or name == '':
            messages.error(request, "Question can't be blank.")
            return render(request, template, {'data':data})
        if desc.isspace() or desc == '':
            messages.error(request, "Answer can't be blank.")
            return render(request, template, {'data':data})
        faq = FAQ.objects.create(name=name, answer=desc, is_active=True)
        faq.save()
        messages.success(request, "Successfully Added!")
        return redirect('faq_listing')
    return render(request, template)

@admin_only
def faqEdit(request, slug):
    template = 'admin/faq-management/edit.html'
    faq = FAQ.objects.get(slug=slug)
    if request.method=="POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        if name.isspace() or name == '':
            messages.error(request, "Question can't be blank.")
            return render(request, template, {'faq':faq})
        if desc.isspace() or desc == '':
            messages.error(request, "Answer can't be blank.")
            return render(request, template, {'faq':faq})
        faq.name = name
        faq.answer = desc
        faq.save()
        messages.success(request, "Successfully updated!")
        return redirect('faq_listing')
    return render(request, template, {'faq':faq})

#-----------------------------faq-end----------------------------------

#-----------------------------term & conditions------------------------
@admin_only
def termsEdit(request):
    template = 'admin/terms_conditions-management/edit.html'
    terms = TermsCondition.objects.all().first()
    if request.method=="POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        if name.isspace() or name == '':
            messages.error(request, "Title can't be blank.")
            return render(request, template, {'terms':terms})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'terms':terms})
        terms.name = name
        terms.desc = desc
        terms.save()
        messages.success(request, "Successfully updated!")
        return redirect('edit_terms_condition')
    return render(request, template, {'terms':terms})

#------------------------------end------------------------------------------------

#-----------------------------Privacy Policy------------------------
@admin_only
def privacyPolicyEdit(request):
    template = 'admin/privacy_policy-management/edit.html'
    policy = PrivacyPolicy.objects.all().first()
    if request.method=="POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        if name.isspace() or name == '':
            messages.error(request, "Title can't be blank.")
            return render(request, template, {'policy':policy})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'policy':policy})
        policy.name = name
        policy.desc = desc
        policy.save()
        messages.success(request, "Successfully updated!")
        return redirect('edit_privacy_policy')
    return render(request, template, {'policy':policy})

#------------------------------end------------------------------------------------


@admin_only
def walletListing(request):
    template = 'admin/wallet-management/listing.html'
    wallet = LenderWallet.objects.all().order_by('-id')
    p = Paginator(wallet, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'wallet':wallet, 'page_obj':page_obj})

@admin_only
def walletView(request, slug):
    template = 'admin/wallet-management/view.html'
    wallet = LenderWallet.objects.get(slug=slug)
    wallet_amount = DwollaCheckBalanceAPI.get_balance(wallet.wallet_id)
    wallet_transaction = DwollaCustomer.objects.get(user_id=wallet.user_id)
    transactions = DwollaTransactionHistoryAPI.all_transactions(wallet_transaction.dwolla_id)
    p = Paginator(transactions, 5)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'wallet':wallet, 'wallet_amount':wallet_amount, 'page_obj':page_obj, 'transactions':transactions})

@admin_only
def walletEdit(request, slug):
    template = 'admin/wallet-management/edit.html'
    wallet = LenderWallet.objects.get(slug=slug)
    wallet_amount = DwollaCheckBalanceAPI.get_balance(wallet.wallet_id)
    if request.method=="POST":
        status = request.POST.get('status')
        wallet.status = status
        wallet.save()
        messages.success(request, "Successfully updated!")
        return redirect('wallet_listing')
    return render(request, template, {'wallet':wallet, 'wallet_amount':wallet_amount})

@admin_only
def walletAmountLimitEdit(request):
    template = 'admin/wallet-management/wallet-edit.html'
    wallet = WalletAmountLimit.objects.get(id=1)
    if request.method=="POST":
        amount = request.POST.get('amount')
        if amount.isspace() or amount == '':
            messages.error(request, "Amount can't be blank.")
            return render(request, template, {'amount':amount})
        wallet.amount = amount
        wallet.save()
        messages.success(request, "Successfully updated!")
        return redirect('edit_wallet_amount')
    return render(request, template, {'wallet':wallet})

#-----------------------address CURD----------------------------
@admin_only
def addressEdit(request, slug):
    template = 'admin/address-management/edit.html'
    address_data = Address.objects.get(slug=slug)
    if request.method=="POST":
        address_title = request.POST.get('address_title')
        address = request.POST.get('address')
        area = request.POST.get('area')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zipcode = request.POST.get('zipcode')
        landmark = request.POST.get('landmark')
        phone_number = request.POST.get('phone_number')
        if address_title.isspace() or address_title == '':
            messages.error(request, "Address title can't be blank.")
            return render(request, template, {'address_data':address_data})
        if address.isspace() or address == '':
            messages.error(request, "Address can't be blank.")
            return render(request, template, {'address_data':address_data})
        if area.isspace() or area == '':
            messages.error(request, "Area can't be blank.")
            return render(request, template, {'address_data':address_data})
        if city.isspace() or city == '':
            messages.error(request, "City can't be blank.")
            return render(request, template, {'address_data':address_data})
        if state.isspace() or state == '':
            messages.error(request, "State can't be blank.")
            return render(request, template, {'address_data':address_data})
        if zipcode.isspace() or zipcode == '':
            messages.error(request, "Zipcode can't be blank.")
            return render(request, template, {'address_data':address_data})
        if landmark.isspace() or landmark == '':
            messages.error(request, "Landmark can't be blank.")
            return render(request, template, {'address_data':address_data})
        if phone_number.isspace() or phone_number == '':
            messages.error(request, "Phone number can't be blank.")
            return render(request, template, {'address_data':address_data})
        address_data.address_title = address_title
        address_data.address = address
        address_data.area = area
        address_data.city = city
        address_data.state = state
        address_data.zipcode = zipcode
        address_data.landmark = landmark
        address_data.phone_number = phone_number
        address_data.save()
        messages.success(request, "Successfully updated!")
        return redirect('view_borrower', address_data.user.slug)
    return render(request, template, {'address_data':address_data})

@admin_only
def addressAdd(request, slug):
    user = User.objects.get(slug=slug)
    template = 'admin/address-management/add.html'
    if request.method=="POST":
        data = request.POST
        address_title = request.POST.get('address_title')
        address = request.POST.get('address')
        area = request.POST.get('area')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zipcode = request.POST.get('zipcode')
        landmark = request.POST.get('landmark')
        phone_number = request.POST.get('phone_number')
        if address_title.isspace() or address_title == '':
            messages.error(request, "Address title can't be blank.")
            return render(request, template, {'data':data})
        if address.isspace() or address == '':
            messages.error(request, "Address can't be blank.")
            return render(request, template, {'data':data})
        if area.isspace() or area == '':
            messages.error(request, "Area can't be blank.")
            return render(request, template, {'data':data})
        if city.isspace() or city == '':
            messages.error(request, "City can't be blank.")
            return render(request, template, {'data':data})
        if state.isspace() or state == '':
            messages.error(request, "State can't be blank.")
            return render(request, template, {'data':data})
        if zipcode.isspace() or zipcode == '':
            messages.error(request, "Zipcode can't be blank.")
            return render(request, template, {'data':data})
        if landmark.isspace() or landmark == '':
            messages.error(request, "Landmark can't be blank.")
            return render(request, template, {'data':data})
        if phone_number.isspace() or phone_number == '':
            messages.error(request, "Phone number can't be blank.")
            return render(request, template, {'data':data})
        user_address = Address.objects.create(address_title = address_title, address = address, area = area, city = city,
        state = state, zipcode = zipcode, landmark = landmark, phone_number = phone_number, user_id=user.id)
        user_address.save()
        messages.success(request, "Successfully added.")
        return redirect('view_borrower', user.slug)
    return render(request, template, {'user':user})

@admin_only
def addressDelete(request, slug):
    try:
        address = Address.objects.get(slug=slug)
    except:
        address = None
    if address:
        address.delete()
        messages.success(request, "Deleted.")
        return redirect('view_borrower', address.user.slug)
    else:
        messages.error(request, "Address not found.")
        return redirect('view_borrower', address.user.slug)

#---------------------loan CURD--------------------
@admin_only
def allLoanUser(request):
    template = 'admin/loan-management/active-loan/listing.html'
    if request.method == 'POST':
        data = request.POST
        search_loan = BorrowerRequestAmount.objects.filter(approve=1, reject=0).filter(
            Q(user__name__contains=data['search_box'])|
            Q(lender__name__contains=data['search_box'])|
            Q(amount__contains=data['search_box']))
        p = Paginator(search_loan, 10)
        page_number = request.GET.get('page')
        try:
            page_obj = p.get_page(page_number) 
        except PageNotAnInteger:
            page_obj = p.page(1)
        except EmptyPage:
            page_obj = p.page(p.num_pages)
        context = {
            'page_obj':page_obj,
            'search_loan':search_loan,
            'search_loan':search_loan.count(),
            'search_object':data['search_box'],
            'search_record':True}
        return render(request, template, context)
    all_loan = BorrowerRequestAmount.objects.filter(approve=1).order_by('-id')
    p = Paginator(all_loan, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'all_loan':all_loan, 'page_obj':page_obj})

@admin_only
def LoanView(request, slug):
    template = 'admin/loan-management/active-loan/view.html'
    try:
        loan_view = BorrowerRequestAmount.objects.get(slug=slug)
    except:
        loan_view = None

    payload = {
        "amount": "10500",
        "fee": "09.01",
        "tenure": "9",
        "start_date": "2023-03-29"
    }
    serializer = EMICalculationSerializer(data=payload, context={'user_id':request.user.id})
    if serializer.is_valid():
        data = serializer.data
    else:
        data = None
    return render(request, template, {'loan_view':loan_view, 'api_data':data})

@admin_only
def loanLimitEdit(request):
    template = 'admin/loan-management/loan-edit.html'
    loan = LoanManagement.objects.get(id=1)
    if request.method=="POST":
        amount = request.POST.get('amount')
        interest = request.POST.get('interest')
        tenure = request.POST.get('tenure')
        commission = request.POST.get('commission')
        loan_request = request.POST.get('loan_request')
        loan_reject = request.POST.get('loan_reject')
        blocked_days = request.POST.get('blocked_days')
        commission_type = request.POST.get('commission_type')
        if amount.isspace() or amount == '':
            messages.error(request, "Amount can't be blank.")
            return render(request, template, {'loan':loan})
        if interest.isspace() or interest == '':
            messages.error(request, "Interest can't be blank.")
            return render(request, template, {'loan':loan})
        if tenure.isspace() or tenure == '':
            messages.error(request, "Tenure can't be blank.")
            return render(request, template, {'loan':loan})
        if commission.isspace() or commission == '':
            messages.error(request, "Commission can't be blank.")
            return render(request, template, {'loan':loan})
        if loan_request.isspace() or loan_request == '':
            messages.error(request, "Loan request can't be blank.")
            return render(request, template, {'loan':loan})
        if loan_reject.isspace() or loan_reject == '':
            messages.error(request, "Loan reject can't be blank.")
            return render(request, template, {'loan':loan})
        if blocked_days.isspace() or blocked_days == '':
            messages.error(request, "Blocked days can't be blank.")
            return render(request, template, {'loan':loan})
        if not commission_type:
            messages.error(request, "Commission type can't be blank.")
            return render(request, template, {'loan':loan})
        loan.amount = amount
        loan.interest = interest
        loan.tenure_month = tenure
        loan.commission = commission
        loan.loan_request = loan_request
        loan.loan_reject = loan_reject
        loan.blocked_days = blocked_days
        loan.commission_type = commission_type
        loan.last_modified = datetime.now()
        loan.save()
        messages.success(request, "Successfully updated!")
        return redirect('edit_loan')
    return render(request, template, {'loan':loan})

#-----------------------------Fake Email Blocked-CURD----------------------------------
@admin_only
def fakeEmailListing(request):
    template = 'admin/fake-email-management/listing.html'
    block_email = BlockEmailDomain.objects.all().order_by('-id')
    p = Paginator(block_email, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'block_email':block_email, 'page_obj':page_obj})

@admin_only
def fakeEmailAdd(request): 
    template = 'admin/fake-email-management/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        domain = request.POST.get('domain')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'data':data})
        if domain.isspace() or domain == '':
            messages.error(request, "Domain can't be blank.")
            return render(request, template, {'data':data})
        block_email = BlockEmailDomain.objects.create(name=name, domain=domain, is_active=True)
        block_email.save()
        messages.success(request, "Successfully Added!")
        return redirect('fake_email_listing')
    return render(request, template)

@admin_only
def fakeEmailEdit(request, slug):
    template = 'admin/fake-email-management/edit.html'
    block_email = BlockEmailDomain.objects.get(slug=slug)
    if request.method=="POST":
        name = request.POST.get('name')
        domain = request.POST.get('domain')
        is_active = request.POST.get('is_active')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'block_email':block_email})
        if domain.isspace() or domain == '':
            messages.error(request, "Domain can't be blank.")
            return render(request, template, {'block_email':block_email})
        block_email.name = name
        block_email.domain = domain
        if is_active:
            block_email.is_active = is_active
        block_email.save()
        messages.success(request, "Successfully updated!")
        return redirect('fake_email_listing')
    return render(request, template, {'block_email':block_email})

@admin_only
def fakeEmailDelete(request, slug):
    try:
        block_email = BlockEmailDomain.objects.get(slug=slug)
    except:
        block_email = None
    if block_email:
        block_email.delete()
        messages.success(request, "Deleted.")
        return redirect('fake_email_listing')
    else:
        messages.error(request, "Domain not found.")
        return redirect('fake_email_listing')

#-----------------------------Plan management-CURD----------------------------------
@admin_only
def planFeatureListing(request):
    template = 'admin/plan-management/listing.html'
    plan = PlanFeature.objects.all().order_by('-id')
    p = Paginator(plan, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    
    return render(request, template, {'plan':plan, 'page_obj':page_obj})

@admin_only
def planFeatureAdd(request): 
    template = 'admin/plan-management/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        if name.isspace() or name == '':
            messages.error(request, "Feature Name can't be blank.")
            return render(request, template, {'data':data})
        plan = PlanFeature.objects.create(name=name, is_active=True)
        plan.save()
        messages.success(request, "Successfully Added!")
        return redirect('feature_listing')
    return render(request, template)

@admin_only
def planFeatureEdit(request, slug):
    template = 'admin/plan-management/edit.html'
    plan = PlanFeature.objects.get(slug=slug)
    if request.method=="POST":
        name = request.POST.get('name')
        is_premium = request.POST.get('is_premium')
        is_active = request.POST.get('is_active')
        if name.isspace() or name == '':
            messages.error(request, "Feature Name can't be blank.")
            return render(request, template, {'plan':plan})
        plan.name = name
        if is_active:
            plan.is_active = is_active
        if is_premium:
            plan.is_premium = is_premium
        plan.save()
        messages.success(request, "Successfully updated!")
        return redirect('feature_listing')
    return render(request, template, {'plan':plan})

# @admin_only
# def fakeEmailDelete(request, slug):
#     try:
#         block_email = BlockEmailDomain.objects.get(slug=slug)
#     except:
#         block_email = None
#     if block_email:
#         block_email.delete()
#         messages.success(request, "Deleted.")
#         return redirect('fake_email_listing')
#     else:
#         messages.error(request, "Domain not found.")
#         return redirect('fake_email_listing')

@admin_only
def activeSubscriptionUser(request):
    template = 'admin/subscription-management/listing.html'
    active_user = UserSubscription.objects.filter(status='ACTIVE')
    p = Paginator(active_user, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'page_obj':page_obj, 'active_user':active_user})

#-----------------------------User Subscription Plan-CURD----------------------------------
@admin_only
def subscriptionPlanListing(request):
    template = 'admin/subscription-management/user-subscription/listing.html'
    subscription_plan = SubscriptionPlan.objects.all().order_by('-id')
    p = Paginator(subscription_plan, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'subscription_plan':subscription_plan, 'page_obj':page_obj})

@admin_only
def subscriptionPlanAdd(request): 
    template = 'admin/subscription-management/user-subscription/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        original_price = request.POST.get('original_price')
        interval = request.POST.get('interval')
        recurring_type = request.POST.get('recurring_type')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'data':data})
        if original_price.isspace() or original_price == '':
            messages.error(request, "Price can't be blank.")
            return render(request, template, {'data':data})
        if not len(original_price) <= 2 or not len(original_price) >= 1:
            messages.error(request, "Price must be valid.")
            return render(request, template, {'data':data})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'data':data})
        try:
            if int(original_price) != 0 or int(original_price) != 00: 
                stripe_product = stripe.Product.create(name=name)
                stripe_price = stripe.Price.create(
                    unit_amount=original_price,
                    currency="usd",
                    recurring={"interval": 'month' if interval == 'MONTHLY' else 'annually'},
                    product=stripe_product.id,
                    )
                SubscriptionPlan.objects.create(name=name, original_price=original_price, description=desc, 
                interval=interval, recurring_type=recurring_type, is_active=True, price_id=stripe_price.id, product_id=stripe_product.id)
                messages.success(request, "Successfully Added!")
                return redirect('subscription_plan_listing')
            else:
                SubscriptionPlan.objects.create(name=name, original_price=original_price, description=desc, 
                interval=interval, is_active=True, is_free=True)
                messages.success(request, "Successfully Added!")
                return redirect('subscription_plan_listing')
        except TypeError as e:
            messages.error(request, e)
            return redirect('subscription_plan_listing')
        except ValueError as e:
            messages.error(request, e)
            return redirect('subscription_plan_listing')
        except stripe.error.CardError as e:
            messages.error(request, e)
            return redirect('subscription_plan_listing')
        except Exception as e:
            messages.error(request, e)
            return redirect('subscription_plan_listing')
    return render(request, template)

@admin_only
def subscriptionPlanEdit(request, slug):
    template = 'admin/subscription-management/user-subscription/edit.html'
    subscription_plan = SubscriptionPlan.objects.get(slug=slug)
    if request.method=="POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        recurring_type = request.POST.get('recurring_type')
        is_active = request.POST.get('is_active')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'subscription_plan':subscription_plan})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'subscription_plan':subscription_plan})
        subscription_plan.name = name
        subscription_plan.description = desc
        subscription_plan.recurring_type = recurring_type
        if is_active:
            subscription_plan.is_active = is_active
        subscription_plan.save()
        messages.success(request, "Successfully updated!")
        return redirect('subscription_plan_listing')
    return render(request, template, {'subscription_plan':subscription_plan})

@admin_only
def subscriptionPlanDelete(request, slug):
    try:
        subscription_plan = SubscriptionPlan.objects.get(slug=slug)
    except:
        subscription_plan = None
    if subscription_plan:
        subscription_plan.delete()
        messages.success(request, "Deleted.")
        return redirect('subscription_plan_listing')
    else:
        messages.error(request, "Subscription not found.")
        return redirect('subscription_plan_listing')

@admin_only
def subscriptionPlanView(request, slug):
    template = 'admin/subscription-management/user-subscription/view.html'
    try:
        subscription_plan = SubscriptionPlan.objects.get(slug=slug)
    except:
        subscription_plan = None
    if subscription_plan:
        return render(request, template, {'subscription_plan':subscription_plan})
    else:
        messages.error(request, "Subscription plan not found.")
        return redirect('subscription_plan_listing')

#---------------Tier CURD--------------------
@admin_only
def tierListing(request):
    template = 'admin/tier-management/listing.html'
    store_tier = StoreTier.objects.all().order_by('-id')
    p = Paginator(store_tier, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'store_tier':store_tier, 'page_obj':page_obj})

@admin_only
def tierView(request, slug):
    template = 'admin/tier-management/view.html'
    store_tier = StoreTier.objects.get(slug=slug)
    return render(request, template, {'store_tier':store_tier})

@admin_only
def tierDelete(request, slug):
    try:
        store_tier = StoreTier.objects.get(slug=slug)
    except:
        store_tier = None
    if store_tier:
        store_tier.delete()
        messages.success(request, "Deleted.")
        return redirect('store_tier_listing')
    else:
        messages.error(request, "Tier not found.")
        return redirect('store_tier_listing')

@admin_only
def tierAdd(request):
    template = 'admin/tier-management/add.html'
    if request.method=="POST":
        data = request.POST
        tier = request.POST.get('tier')
        starting_price = request.POST.get('starting_price')
        end_price = request.POST.get('end_price')
        month = request.POST.get('month')
        interest = request.POST.get('interest')
        desc = request.POST.get('desc')
        if tier == '---select---':
            messages.error(request, "Please select tier category.")
            return render(request, template, {'data':data})
        if starting_price.isspace() or starting_price == '':
            messages.error(request, "Starting Price can't be blank.")
            return render(request, template, {'data':data})
        if end_price.isspace() or end_price == '':
            messages.error(request, "Ending Price can't be blank.")
            return render(request, template, {'data':data})
        if month.isspace() or month == '':
            messages.error(request, "Month can't be blank.")
            return render(request, template, {'data':data})
        if interest.isspace() or interest == '':
            messages.error(request, "Interest can't be blank.")
            return render(request, template, {'data':data})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'data':data})
        store_tier = StoreTier.objects.create(name=tier, category=tier, starting_price=starting_price, end_price=end_price, interest=interest,
        interval_month=month, description=desc, is_active=True)
        store_tier.save()
        messages.success(request, "Successfully Added!")
        return redirect('store_tier_listing')
    return render(request, template)

@admin_only
def tierEdit(request, slug):
    template = 'admin/tier-management/edit.html'
    store_tier = StoreTier.objects.get(slug=slug)
    if request.method=="POST":
        tier = request.POST.get('tier')
        starting_price = request.POST.get('starting_price')
        end_price = request.POST.get('end_price')
        month = request.POST.get('month')
        interest = request.POST.get('interest')
        desc = request.POST.get('desc')
        if tier == '---select---':
            messages.error(request, "Please select tier category.")
            return render(request, template, {'store_tier':store_tier})
        if starting_price.isspace() or starting_price == '':
            messages.error(request, "Starting Price can't be blank.")
            return render(request, template, {'store_tier':store_tier})
        if end_price.isspace() or end_price == '':
            messages.error(request, "Ending Price can't be blank.")
            return render(request, template, {'store_tier':store_tier})
        if month.isspace() or month == '':
            messages.error(request, "Month can't be blank.")
            return render(request, template, {'store_tier':store_tier})
        if interest.isspace() or interest == '':
            messages.error(request, "Interest can't be blank.")
            return render(request, template, {'store_tier':store_tier})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'store_tier':store_tier})
        store_tier.category = tier
        store_tier.starting_price = starting_price
        store_tier.end_price = end_price
        store_tier.interest = interest
        store_tier.interval_month = month
        store_tier.description = desc
        store_tier.save()
        messages.success(request, "Successfully updated!")
        return redirect('store_tier_listing')
    return render(request, template, {'store_tier':store_tier})


#-----------------------------Store Subscription Plan-CURD----------------------------------
@admin_only
def storeSubscriptionPlanListing(request):
    template = 'admin/subscription-management/store-subscription/listing.html'
    subscription_plan = StoreSubscriptionPlan.objects.all().order_by('-id')
    p = Paginator(subscription_plan, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'subscription_plan':subscription_plan, 'page_obj':page_obj})

@admin_only
def storeSubscriptionPlanAdd(request): 
    template = 'admin/subscription-management/store-subscription/add.html'
    if request.method=="POST":
        data = request.POST
        name = request.POST.get('name')
        price = request.POST.get('price')
        interval = request.POST.get('interval')
        desc = request.POST.get('desc')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'data':data})
        if price.isspace() or price == '':
            messages.error(request, "Price can't be blank.")
            return render(request, template, {'data':data})
        if not len(price) <= 2 or not len(price) >= 1:
            messages.error(request, "Price must be valid.")
            return render(request, template, {'data':data})
        if interval.isspace() or interval == '':
            messages.error(request, "Interval can't be blank.")
            return render(request, template, {'data':data})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'data':data})
        try:
            stripe_product = stripe.Product.create(name=name)
            stripe_price = stripe.Price.create(
                unit_amount=price,
                currency="usd",
                recurring={"interval": 'month' if interval == 'MONTHLY' else 'annually'},
                product=stripe_product.id,
                )
            StoreSubscriptionPlan.objects.create(name=name, price_id=stripe_price.id,
            price=price, description=desc, interval=interval, product_id=stripe_product.id)
            messages.success(request, "Successfully Added!")
            return redirect('store_subscription_plan_listing')
        except TypeError as e:
            messages.error(request, e)
            return redirect('subscription_plan_listing')
        except ValueError as e:
            messages.error(request, e)
            return redirect('subscription_plan_listing')
        except stripe.error.CardError as e:
            messages.error(request, e)
            return redirect('subscription_plan_listing')
        except Exception as e:
            messages.error(request, e)
            return redirect('subscription_plan_listing')
    return render(request, template)

@admin_only
def storeSubscriptionPlanEdit(request, slug):
    template = 'admin/subscription-management/store-subscription/edit.html'
    subscription_plan = StoreSubscriptionPlan.objects.get(slug=slug)
    if request.method=="POST":
        name = request.POST.get('name')
        desc = request.POST.get('desc')
        is_active = request.POST.get('is_active')
        if name.isspace() or name == '':
            messages.error(request, "Name can't be blank.")
            return render(request, template, {'subscription_plan':subscription_plan})
        if desc.isspace() or desc == '':
            messages.error(request, "Description can't be blank.")
            return render(request, template, {'subscription_plan':subscription_plan})
        subscription_plan.name = name
        subscription_plan.description = desc
        if is_active:
            subscription_plan.is_active = is_active
        subscription_plan.save()
        messages.success(request, "Successfully updated!")
        return redirect('store_subscription_plan_listing')
    return render(request, template, {'subscription_plan':subscription_plan})

@admin_only
def storeSubscriptionPlanDelete(request, slug):
    try:
        subscription_plan = StoreSubscriptionPlan.objects.get(slug=slug)
    except:
        subscription_plan = None
    if subscription_plan:
        subscription_plan.delete()
        messages.success(request, "Deleted.")
        return redirect('store_subscription_plan_listing')
    else:
        messages.error(request, "Subscription not found.")
        return redirect('store_subscription_plan_listing')

@admin_only
def storeSubscriptionPlanView(request, slug):
    template = 'admin/subscription-management/store-subscription/view.html'
    try:
        subscription_plan = StoreSubscriptionPlan.objects.get(slug=slug)
    except:
        subscription_plan = None
    if subscription_plan:
        return render(request, template, {'subscription_plan':subscription_plan})
    else:
        messages.error(request, "Subscription plan not found.")
        return redirect('store_subscription_plan_listing')

#-----------------------------------Admin Payment Settings----------------------------------

@admin_only
def adminEarning(request):
    template = 'admin/admin-dwolla/earning.html'
    admin_amount = AdminEarning.objects.all()
    pending_amount = admin_amount.aggregate(pending_amount = Sum('pending_amount'))
    received_amount = admin_amount.aggregate(received_amount = Sum('received_amount'))
    if not received_amount['received_amount']:
        received_amount['received_amount'] = 0
    if not pending_amount['pending_amount']:
        pending_amount['pending_amount'] = 0
    subscription_earning = UserSubscription.objects.aggregate(subscription_earning=Sum('amount'))
    total_profit = subscription_earning['subscription_earning'] + received_amount['received_amount']
    admin_earning = AdminEarning.objects.annotate(month=TruncMonth("created")).values("month").annotate(earning=Sum('received_amount'))
    month = {
        'January': {'earning':0},
		'February': {'earning':0},
		'March': {'earning':0},
		'April': {'earning':0},
		'May': {'earning':0},
		'June': {'earning':0},
		'July': {'earning':0},
		'August': {'earning':0},
		'September': {'earning':0},
		'October': {'earning':0},
		'November': {'earning':0},
		'December': {'earning':0}
        }
    for i in admin_earning:
        month[i.get('month').strftime("%B")] = {'earning': i.get('earning')}
    context = {
        'pending_amount':pending_amount,
        'received_amount':received_amount,
        'month':month,
        'subscription_earning': round(subscription_earning['subscription_earning'], 2),
        'total_profit': round(total_profit, 2)
    }
    return render(request, template, context)

@admin_only
def adminAccountEdit(request):
    template = 'admin/admin-dwolla/dwolla-edit.html'
    dwolla_account = AdminAccount.objects.all().first()
    admin_balance = DwollaCheckBalanceAPI.get_balance(dwolla_account.wallet_id)
    # transactions = DwollaTransactionHistoryAPI.all_transactions(dwolla_account.wallet_id)
    # p = Paginator(transactions, 5)
    # page_number = request.GET.get('page')
    # try:
    #     page_obj = p.get_page(page_number) 
    # except PageNotAnInteger:
    #     page_obj = p.page(1)
    # except EmptyPage:
    #     page_obj = p.page(p.num_pages)
    if request.method=="POST":
        wallet_id = request.POST.get('wallet_id')
        if wallet_id.isspace() or wallet_id == '':
            messages.error(request, "Wallet can't be blank.")
            return render(request, template, {'dwolla_account':dwolla_account})
        dwolla_account.wallet_id = wallet_id
        dwolla_account.save()
        messages.success(request, "Successfully updated!")
        return redirect('dwolla_account')
    return render(request, template, {'dwolla_account':dwolla_account, 'admin_balance':admin_balance})

@admin_only
def lenderEarning(request):
    template = 'admin/admin-dwolla/lender_earning.html'
    users = User.objects.filter(is_superuser=False, is_active=True, is_verified=True)
    p = Paginator(users, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number) 
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    return render(request, template, {'users':users, 'page_obj':page_obj})

def TestPdf(request):
    return FileResponse(generate_pdf(), filename='hello.pdf')

@csrf_exempt
def TestSubscriptionCompletedwebhook(request):
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    event = None
    payload = request.body
    sig_header = request.headers['STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Handle the event
    if event['type'] == 'invoice.paid':
        subscription_schedule = event['data']['object']
        print(subscription_schedule, '+++++++++++++++++')
    if event['type'] == 'test_helpers.test_clock':
        subscription_schedule = event['data']['object']
        print(subscription_schedule, '00000000000000000000')
    if event['type'] == 'test_helpers.test_clock.advancing':
        subscription_schedule = event['data']['object']
        print(subscription_schedule, '11111111111111111')
    if event['type'] == 'test_helpers.test_clock.ready':
        subscription_schedule = event['data']['object']
        print(subscription_schedule, '22222222222222222222')
    if event['type'] == 'charge.failed':
        subscription_schedule = event['data']['object']
        print(subscription_schedule, '3333333333333333333')
    if event['type'] == 'payment_intent.payment_failed':
        subscription_schedule = event['data']['object']
        print(subscription_schedule, '----------')
    else:
      print('Unhandled event type {}'.format(event['type']))

    return JsonResponse({
        'success':True
    })
