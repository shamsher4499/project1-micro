from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.utils.html import strip_tags
from superadmin.models import User, EmailTemplate
from .custom_threading import EmailThread
from datetime import datetime
import random
import string
from dataclasses import dataclass
from django.utils.html import strip_tags

@dataclass
class DefaultEmailTemplate:
    body: str

    def email_otp(self) -> str:
        subject = 'Email verification otp'
        return subject, self.body

    def send_credentials(self) -> str:
        subject = 'Your Credentials is here'
        return subject, self.body

    def send_alert(self) -> str:
        subject = 'Your Password has been changed'
        return subject, self.body

    def send_login_alert(self) -> str:
        subject = 'Login Alert'
        return subject, self.body


def sendOTP(user):
    try:
        email = EmailTemplate.objects.get(name='Verify Email OTP')
    except:
        email = None
    otp = random.randint(1000, 9999)
    if email:
        subject = email.name
        data = email.editor
        message = data.replace('name', user.name).replace('otp', str(otp))
        EmailThread(subject, message, [user.email]).start()
        user.otp = otp
        user.save()
    else:
        otp_data = DefaultEmailTemplate(f'Hello {user.name},\nYour OTP is {otp}\nThanks')
        subject, message = otp_data.email_otp()
        EmailThread(subject, message, [user.email]).start()
        user.otp = otp
        user.save()

def sendCredentials(user):
    try:
        email = EmailTemplate.objects.get(name='Your Credentials details are here')
    except:
        email = None
    generate_password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
    if email:
        subject = email.name
        data = email.editor
        message = data.replace('name', user.name).replace('email', user.email).replace('password', generate_password)
        EmailThread(subject, message, [user.email]).start()
        user.set_password(generate_password)
        user.save()
    else:
        otp_data = DefaultEmailTemplate(f'Hello {user.name},\nYour email is :{user.email}\nYour Password is :{generate_password}\n\nThanks & Regards\nCashuu Team')
        subject, message = otp_data.send_credentials()
        EmailThread(subject, message, [user.email]).start()
        user.set_password(generate_password)
        user.save()

def sendAlert(user, location):
    try:
        email = EmailTemplate.objects.get(name='Your Password has been changed!')
    except:
        email = None
    if email:
        subject = email.name
        data = email.editor
        if user.name != None:
            message = data.format(name=user.name, ip_address=location.get("ip"), city=location.get("city"), region=location.get("region"), country=location.get("country"))
        else:
            message = data.format(name='User')
        EmailThread(subject, message, [user.email]).start()
    else:
        otp_data = DefaultEmailTemplate(f'Hello {user.name},\nIP address is :{location.get("ip")}\nCity is :{location.get("city")}\nRegion is :{location.get("region")}Country is :{location.get("country")}\n\nThanks & Regards\nCashuu Team')
        subject, message = otp_data.send_alert()
        EmailThread(subject, message, [user.email]).start()

def loginAlert(user_data, location):
    try:
        email = EmailTemplate.objects.get(name='Login Alert')
    except:
        email = None
    if location.get("city") != None:
        city = location.get("city")
        country = location.get("country")
        region = location.get("region")
    else:
        city='Los Angeles' 
        region='California'
        country='United States'
    if email:
        user = User.objects.get(email=user_data)
        subject = email.name
        data = email.editor
        message = data.format(name=user.name if user.name else 'User', last_login=user.last_login, ip_address=location.get("ip"), city=city, region=region, country=country)
        EmailThread(subject, message, [user.email]).start() 
    else:
        otp_data = DefaultEmailTemplate(f'Hello {user.name if user.name else "User"},\nIP address is :{location.get("ip")}\nCity is :{city}\nRegion is :{region}Country is :{country}\n\nThanks & Regards\nCashuu Team')
        subject, message = otp_data.send_login_alert()
        EmailThread(subject, message, [user.email]).start()

def changePasswordOTP(user):
    email = EmailTemplate.objects.get(name='Change Password OTP')
    otp = random.randint(1000, 9999)
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, otp=otp)
        EmailThread(subject, message, [user.email]).start()
        user.otp = otp
        user.otp_sent_time = datetime.now()
        user.save()
    else:
        message = data.format(name='User', otp=otp)
        EmailThread(subject, message, [user.email]).start()
        user.otp = otp
        user.otp_sent_time = datetime.now()
        user.save()

def sendInquiryReply(user):
    email = EmailTemplate.objects.get(name='Your Query has been updated')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, subject=user.subject, created=user.created, message=user.message, answer=user.answer)
        EmailThread(subject, message, [user.email]).start()
    else:
        message = data.format(name='User')
        EmailThread(subject, message, [user.email]).start()

def sendApproveMail(user):
    email = EmailTemplate.objects.get(name='Your account has been approved')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, email=user.email)
        EmailThread(subject, message, [user.email]).start()
    else:
        message = data.format(name='User', email='None')
        EmailThread(subject, message, [user.email]).start()

def accountSuspended(user):
    email = EmailTemplate.objects.get(name='Your account suspended by admin')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, email=user.email)
        EmailThread(subject, message, [user.email]).start()
    else:
        message = data.format(name='User', email='None')
        EmailThread(subject, message, [user.email]).start()

def accountReject(user):
    email = EmailTemplate.objects.get(name='Your account rejected by admin')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, email=user.email)
        EmailThread(subject, message, [user.email]).start()
    else:
        message = data.format(name='User', email=user.email)
        EmailThread(subject, message, [user.email]).start()

def subscriptionSucess(user):
    email = EmailTemplate.objects.get(name='Your subscription started')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, email=user.email)
        EmailThread(subject, message, [user.email]).start()
    else:
        message = data.format(name='User', email=user.email)
        EmailThread(subject, message, [user.email]).start()


def subscriptionReject(user):
    email = EmailTemplate.objects.get(name='Your subscription stopped')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, email=user.email)
        EmailThread(subject, message, [user.email]).start()
    else:
        message = data.format(name='User', email=user.email)
        EmailThread(subject, message, [user.email]).start()

def sendDwollaError(user, reason):
    email = EmailTemplate.objects.get(name='Need to sign up again')
    subject = email.name
    data = email.editor
    if user['name'] != '':
        message = data.format(name=user['name'], email=user['email'], reason=reason)
        EmailThread(subject, strip_tags(message), [user['email']]).start()
    else:
        message = data.format(name='User')
        EmailThread(subject, strip_tags(message), [user['email']]).start()