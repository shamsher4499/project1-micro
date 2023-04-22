from django.db import transaction
from dwollav2.error import Error as DwollaError
from api.utils import check_ssn
from api.dwolla_payment import DwollaCustomerAPI, DwollaFundingSourceAPI
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import resolve
from superadmin.models import *
from django.db.models import Q
from app.utils import *
from .email import *
import stripe
from django.contrib.auth.models import auth
from datetime import datetime, timedelta
import json
import threading
from app.custom_threading import threaded_function

def resendAppOTP(slug):
    user = User.objects.get(slug=slug, is_superuser=False)
    if user.otp_sent_time != None:
        filter_date = str(user.otp_sent_time)[:19]
        now_plus_10 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
        if datetime.now() >= now_plus_10:
            changePasswordOTP(user)
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
        changePasswordOTP(user)
        return {
            "status": True,
            "message": "Verification code sent on the mail address. Please check."
            }

def resendEmailVerifyOTP(slug):
    user = User.objects.get(slug=slug, is_superuser=False)
    if user.otp_sent_time != None:
        filter_date = str(user.otp_sent_time)[:19]
        now_plus_10 = datetime.strptime(str(filter_date), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
        if datetime.now() >= now_plus_10:
            sendOTP(user)
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
        sendOTP(user)
        return {
            "status": True,
            "message": "Verification code sent on the mail address. Please check."
            }

def signUpUser(request):
    template_name = 'frontend/auth/signup.html'
    json_data = open("country_code.json")
    country_data = json.load(json_data)
    json1_data = open("states.json")
    states_data = json.load(json1_data)
    if request.method == 'POST':
        data = request.POST
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        select_code = request.POST.get('calling_code')
        name = request.POST.get('first_name', None) + request.POST.get('last_name', None)
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        document = request.FILES.get('document')
        is_checked = request.POST.get('is_checked')

        first_name = request.POST.get('first_name', None)
        last_name = request.POST.get('last_name', None)
        address = request.POST.get('address1', '')
        city = request.POST.get('city', '').upper()
        state = request.POST.get('state_code', '')
        postal_code = request.POST.get('postal_code', '')
        date_of_birth = request.POST.get('date_of_birth', '')
        ssn = request.POST.get('ssn', '')

        if not User.objects.filter(email=email).exists():
            if email.isspace() or email == '' or '@' not in email:
                messages.error(request, "Email can't be blank or email must be valid.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif mobile.isspace() or mobile == '' or len(mobile) != 10 or not mobile.isnumeric():
                messages.error(request, "Mobile can't be blank or Must be 10 digit.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif User.objects.filter(mobile=mobile, mobile_verified=True).exists():
                messages.error(request, "Mobile must be unique.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif name.isspace() or name == '':
                messages.error(request, "Name can't be blank.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif password.isspace() or password == '':
                messages.error(request, "Password can't be blank.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif confirm_password.isspace() or confirm_password == '':
                messages.error(request, "Confirm Password can't be blank.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif not check_password(confirm_password):
                messages.error(request, "Password must have combination of @Sa4 and 8 characters.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif password != confirm_password:
                messages.error(request, "Password not matched.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif document == None:
                messages.error(request, "Document must be .pdf format.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif not (document.name.split('.')[-1]).lower() in docs_type:
                messages.error(request, "Document must be pdf,png,jpeg,xls only.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif not get_size(document):
                messages.error(request, "Document size must be less than 2 MB.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif is_checked != '1':
                messages.error(request, "Please accept terms & conditions.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif first_name.isspace() or first_name == '':
                messages.error(request, "First Name can't be blank.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif last_name.isspace() or last_name == '':
                messages.error(request, "Last Name can't be blank.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif city.isspace() or city == '':
                messages.error(request, "City can't be blank.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif state.isspace() or state == '' or len(city) == 2:
                messages.error(request, "State can't be blank and can contain only 2 letters")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif postal_code.isspace() or postal_code == '' or len(postal_code) > 5 or not postal_code.isnumeric():
                messages.error(request, "Postal Code can't be blank and can contain only 5 numbers")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif date_of_birth.isspace() or date_of_birth == '' or not date_of_birth:
                messages.error(request, "Date of Birth is required.")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})
            elif not check_ssn(ssn):
                messages.error(request, "Please Enter Valid SSN")
                return render(request, template_name, {'data':data, 'country_data':country_data, 'states_data':states_data})

            try:
                # with transaction.atomic():
                calling_code, country_code = select_code.split('$')[0], select_code.split('$')[1]
                user = User(name=name, email=email.lower(), calling_code=calling_code, 
                    country_code=country_code, mobile=mobile, document=document)
                user.set_password(confirm_password)
                customer_data = stripe.Customer.create(
                    name=name,
                    email=email.lower(),
                    phone=mobile
                    )
                user.customer_id = customer_data['id']
                user.save_with_slug()
                sendOTP(user)

                customer = {
                    'firstName': first_name,
                    'lastName': last_name,
                    'email': email,
                    "address1": address,
                    "city": city,
                    "state": state,
                    "postalCode": postal_code,
                    "dateOfBirth": date_of_birth,
                    "ssn": ssn,
                }
                t = threading.Thread(target=threaded_function, args=(customer,user.id))
                t.start()
                messages.success(request, "Verification code has been sent on the mail address.")
                return redirect('email_verify', str(user.slug))
            # except DwollaError as e:
            #     messages.error(request, e.body['_embedded']['errors'][0]['message'])
            #     return redirect('create_dwolla_account')
            except:
                messages.error(request, 'Dwolla facing huge traffic now. Please try again')
                return redirect('create_dwolla_account')
        else:
            messages.error(request, "Email already used!")
            return render(request, template_name, {'data':data,'country_data':country_data, 'states_data':states_data})
    return render(request, template_name, {'country_data':country_data, 'states_data':states_data})

def emailVerify(request, slug):
    template_name = 'frontend/auth/otp.html'
    user = User.objects.get(slug=slug)
    if request.method == 'POST':
        otp1 = request.POST.get('otp1')
        otp2 = request.POST.get('otp2') 
        otp3 = request.POST.get('otp3') 
        otp4 = request.POST.get('otp4') 
        otp = otp1+otp2+otp3+otp4
        if 'resend_otp' in request.POST:
            response = resendEmailVerifyOTP(slug)
            if response['status']:
                messages.success(request, response['message'])
            else:
                messages.info(request, response['message'])
            return redirect('email_verify', slug)
        if otp1.isspace() or otp1 == '' and otp2.isspace() or otp2 == '' and otp3.isspace() or otp3 == '' and otp4.isspace() or otp4 == '':
            messages.error(request, "otp not be blank!")
            return redirect('email_verify', str(user.slug))
        if user.otp != otp:
            messages.error(request, "otp not matched!")
            return redirect('email_verify', str(user.slug))
        else:
            user.is_verified = True
            user.is_active = True
            user.otp = ''
            user.save()
            messages.success(request, "Email successfully verified.")
            return redirect('registration_successfully')
    return render(request, template_name, {'user':user})

def successRegistration(request):
    template_name = 'frontend/auth/success-registration.html'
    if request.META.get('HTTP_REFERER'):
        return render(request, template_name)
    else:
        return redirect('user_sign_in')

def forgetPasswordStep1(request):
    template_name = 'frontend/auth/forgot-password.html'
    if request.method == 'POST':
        data = request.POST
        email = request.POST.get('email')
        if email.isspace() or email == '' or '@' not in email:
            messages.error(request, "Please enter valid email!")
            return render(request, template_name, {'data':data})
        if User.objects.filter(email=email, is_superuser=False).exists():
            user = User.objects.get(email=email)
            changePasswordOTP(user)
            messages.success(request, "otp sent.")
            return redirect('app_forget_password2', str(user.slug))
        else:
            messages.error(request, "email not found!")
            return redirect('app_forget_password1')
    return render(request, template_name)

def forgetPasswordStep2(request, slug):
    template_name = 'frontend/auth/otp.html'
    # if not request.META.get('HTTP_REFERER') or (request.META.get('HTTP_REFERER') and 'forgetPassword-setp1' not in request.META.get('HTTP_REFERER')):
    #     return redirect('user_sign_in')
    user = User.objects.get(slug=slug)
    if request.method == 'POST':
        otp1 = request.POST.get('otp1')
        otp2 = request.POST.get('otp2') 
        otp3 = request.POST.get('otp3') 
        otp4 = request.POST.get('otp4') 
        otp = otp1+otp2+otp3+otp4
        if 'resend_otp' in request.POST:
            response = resendAppOTP(slug)
            if response['status']:
                messages.success(request, response['message'])
            else:
                messages.info(request, response['message'])
            return redirect('app_forget_password2', slug)
        if otp1.isspace() or otp1 == '' and otp2.isspace() or otp2 == '' and otp3.isspace() or otp3 == '' and otp4.isspace() or otp4 == '':
            messages.error(request, "otp not be blank!")
            return redirect('app_forget_password2', str(user.slug))
        if user.otp != otp:
            messages.error(request, "otp not matched!")
            return redirect('app_forget_password2', str(user.slug))
        else:
            user.otp = ""
            user.save()
            messages.success(request, "Email successfully verified.")
            return redirect('app_forget_password3', str(user.slug), str(user.slug_user))
    return render(request, template_name, {'user':user})

def forgetPasswordStep3(request, slug, user_slug):
    template_name = 'frontend/auth/reset-password.html'
    # if not request.META.get('HTTP_REFERER') or (request.META.get('HTTP_REFERER') and 'forgetPassword-setp2' not in request.META.get('HTTP_REFERER')):
    #     return redirect('user_sign_in')
    if request.method == 'POST':
        data = request.POST
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password.isspace() or password == '':
            messages.error(request, "Please enter valid password!")
            return render(request, template_name, {'data':data})
        if confirm_password.isspace() or confirm_password == '':
            messages.error(request, "Please enter valid password!")
            return render(request, template_name, {'data':data})
        if password != confirm_password:
            messages.error(request, "Password not matched!")
            return render(request, template_name, {'data':data})
        if not check_password(confirm_password):
            messages.error(request, "Password must have combination of @Sa4 and 8 characters.")
            return render(request, template_name, {'data':data})
        if User.objects.filter(slug=slug, slug_user=user_slug).exists():
            user = User.objects.get(slug=slug)
            if user.check_password(data["confirm_password"]):
                messages.error(request, "You can't be set old password as new password.")
                return render(request, template_name, {'data':data})
            else:
                user.set_password(confirm_password)
                user.save()
                messages.success(request, "Password successfully changed.")
            return redirect('user_sign_in')
        messages.error(request, "User not found!")
        return render(request, template_name, {'data':data})
    return render(request, template_name)

def signIn(request):
    template_name = 'frontend/auth/login.html'
    if request.method == 'POST':
        data = request.POST
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_mobile = email.isnumeric()
        if is_mobile and len(email) != 10:
            messages.error(request, "Please enter valid Mobile Number!")
            return render(request, template_name, {'data':data})
        elif not is_mobile and (email.isspace() or email == '' or '@' not in email):
            messages.error(request, "Please enter valid email!")
            return render(request, template_name, {'data':data})
        if password.isspace() or password == '':
            messages.error(request, "Please enter valid password!")
            return render(request, template_name, {'data':data})
        user = User.objects.filter(Q(email=email)|Q(mobile=email))
        if user.exists():
            user = user.first()
            if user.is_superuser:
                messages.error(request, "You have no access to login.")
                return redirect('user_sign_in')
            if user.is_store:
                messages.error(request, "You have no access to login.")
                return redirect('user_sign_in')
            if user.is_verified != True:
                sendOTP(user)
                messages.error(request, "Your Email address is not verified yet. Please Check mail.")
                return redirect('email_verify', str(user.slug))
            if user.is_active != True:
                messages.error(request, "Your account not verified by admin.")
                return render(request, template_name, {'data':data})
            if is_mobile and not user.mobile_verified:
                messages.error(request, "Your mobile number not verified yet.")
                return render(request, template_name, {'data':data})
            login_user = auth.authenticate(email=user.email,  password=password)
            if login_user == None:
                messages.error(request, "Invalid email or password!")
                return render(request, template_name, {'data':data})
            else:
                auth.login(request, user)
                messages.success(request, "Login Success.")
                return redirect('home')
                
        else:
            messages.error(request, "Email address not found!")
            return render(request, template_name, {'data':data})
    return render(request, template_name)

def changePassword(request):
    template_name = 'frontend/auth/change-password.html'
    user = request.user
    if request.method == 'POST':
        data = request.POST
        current_password = request.POST.get('current_password')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if current_password.isspace() or current_password == '':
            messages.error(request, "Please enter valid current password!")
            return render(request, template_name, {'data':data})
        if password.isspace() or password == '':
            messages.error(request, "Please enter valid password!")
            return render(request, template_name, {'data':data})
        if confirm_password.isspace() or confirm_password == '':
            messages.error(request, "Please enter valid confirm password!")
            return render(request, template_name, {'data':data})
        if password != confirm_password:
            messages.error(request, "Password not matched!")
            return render(request, template_name, {'data':data})
        if not check_password(confirm_password):
            messages.error(request, "Password must have combination of @Sa4 and 8 characters.")
            return render(request, template_name, {'data':data})
        if not user.check_password(data["current_password"]):
            messages.error(request, "Incorrect current password!")
            return render(request, template_name, {'data':data})
        if user.check_password(data["confirm_password"]):
            messages.error(request, "You can't be set old password as new password.")
            return render(request, template_name, {'data':data})
        else:
            user.set_password(confirm_password)
            user.save()
            auth.login(request, user)
            messages.success(request, "Password successfully changed.")
            return render(request, template_name)
    return render(request, template_name)

def logoutUser(request):
    auth.logout(request)
    messages.success(request, "Successfully Logout")
    return redirect('user_sign_in')