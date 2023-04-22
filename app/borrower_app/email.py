from django.conf import settings
from django.core.mail import send_mail, EmailMessage
import random
from superadmin.models import User, EmailTemplate
import string
import random
import threading
from threading import Thread
from datetime import datetime
from django.utils.html import strip_tags

class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        threading.Thread.__init__(self)

    def run (self):
        msg = EmailMessage(self.subject, strip_tags(self.html_content), settings.EMAIL_HOST_USER, self.recipient_list)
        msg.send()

def sendOTP(user):
    email = EmailTemplate.objects.get(name='Verify Email OTP')
    otp = random.randint(1000, 9999)
    subject = email.name
    data = email.editor
    message = data.replace('name', user.name).replace('otp', str(otp))
    EmailThread(subject, message, [user.email]).start()
    user.otp = otp
    user.save()

def sendCredentials(user):
    email = EmailTemplate.objects.get(name='Your Credentials details are here')
    generate_password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
    subject = email.name
    data = email.editor
    message = data.replace('name', user.name).replace('email', user.email).replace('password', generate_password)
    EmailThread(subject, message, [user.email]).start()
    user.set_password(generate_password)
    user.save()

# def sendAlert(user):
#     email = EmailTemplate.objects.get(name='Your Password has been changed!')
#     subject = email.name
#     data = email.editor
#     if user.name != None:
#         message = data.format(name=user.name)
#         EmailThread(subject, message, [user.email]).start()
#     else:
#         message = data.format(name='User')
#         EmailThread(subject, message, [user.email]).start()

def sendAlert(user, location):
    email = EmailTemplate.objects.get(name='Your Password has been changed!')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, ip_address=location.get("ip"), city=location.get("city"), region=location.get("region"), country=location.get("country"))
        EmailThread(subject, message, [user.email]).start()
    else:
        message = data.format(first_name='User')
        EmailThread(subject, message, [user.email]).start()

def sendAccountBlocked(user, login_time):
    email = EmailTemplate.objects.get(name='Your Account has been blocked!')
    subject = email.name
    data = email.editor
    if user.name != None:
        message = data.format(name=user.name, login_time=login_time)
        EmailThread(subject, message, [user.email]).start()
    else:
        message = data.format(name='User')
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

def sendInqury(inqury):
    email = EmailTemplate.objects.get(name='Your query has been recevied')
    subject = email.name
    data = email.editor
    if inqury.name != None:
        message = data.format(name=inqury.name, subject=inqury.subject, message=inqury.message, created=inqury.created)
        EmailThread(subject, message, [inqury.email]).start()
    else:
        message = data.format(name='User')
        EmailThread(subject, message, [inqury.email]).start()