from superadmin.models import EmailTemplate
from api.custom_threading import EmailThread
from datetime import datetime
import string
import random
from django.utils.html import strip_tags


def sendOTP(user):
    email = EmailTemplate.objects.get(name='Verify Email OTP')
    otp = random.randint(1000, 9999)
    subject = email.name
    data = email.editor
    message = data.replace('name', user.name).replace('otp', str(otp))
    EmailThread(subject, strip_tags(message), [user.email]).start()
    user.otp = otp
    user.save()

def sendCredentials(user):
    email = EmailTemplate.objects.get(name='Your Credentials details are here')
    generate_password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
    subject = email.name
    data = email.editor
    message = data.replace('name', user.name).replace('email', user.email).replace('password', generate_password)
    EmailThread(subject, strip_tags(message), [user.email]).start()
    user.set_password(generate_password)
    user.save()

def sendAlert(user):
    email = EmailTemplate.objects.get(name='Your Password has been changed!')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name)
        EmailThread(subject, strip_tags(message), [user.email]).start()
    else:
        message = data.format(name='User')
        EmailThread(subject, strip_tags(message), [user.email]).start()

def sendAccountBlocked(user, login_time):
    email = EmailTemplate.objects.get(name='Your Account has been blocked!')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, login_time=login_time)
        EmailThread(subject, strip_tags(message), [user.email]).start()
    else:
        message = data.format(name='User')
        EmailThread(subject, strip_tags(message), [user.email]).start()

def changePasswordOTP(user):
    email = EmailTemplate.objects.get(name='Change Password OTP')
    otp = random.randint(1000, 9999)
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, otp=otp)
        EmailThread(subject, strip_tags(message), [user.email]).start()
        user.otp = otp
        user.otp_sent_time = datetime.now()
        user.save()
    else:
        message = data.format(name='User', otp=otp)
        EmailThread(subject, strip_tags(message), [user.email]).start()
        user.otp = otp
        user.otp_sent_time = datetime.now()
        user.save()