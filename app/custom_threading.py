from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import threading
from api.dwolla_payment import DwollaCustomerAPI, DwollaFundingSourceAPI
from superadmin.models import DwollaCustomer, LenderWallet


class EmailThread(threading.Thread):
    """
    The code starts by creating a class called EmailThread.
    The __init__ method of the class is used to initialize the email thread with a subject and html content.
    Next, it creates an instance of this class with a recipient list that includes the user's email address.
    Then, it sends out the message using send().
    The run method starts by creating an instance of EmailMessage which will be sent out to all recipients in its recipient_list variable.
    It then sets up some variables for sending messages such as setting up EMAIL_HOST_USER and settings f
    or sending emails like how many recipients should be included in each email.
    Finally, it calls send() on the newly created object which sends out the message to all recipients
    The code creates a new EmailThread object, which is then passed to the threading.Thread constructor.
    The __init__() method of the threading.Thread class is called on the newly created EmailThread object and 
    it assigns the subject, recipient list and HTML content of the email to its corresponding variables.
    The run() method is then called on this newly created thread which sends an email with the subject and 
    HTML content specified in its __init__() function.
    """
    def __init__(self, subject, html_content, recipient_list):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        threading.Thread.__init__(self)

    def run (self):
        msg = EmailMessage(self.subject, self.html_content, settings.EMAIL_HOST_USER, self.recipient_list)
        msg.send()


def threaded_function(arg1:dict, user_id) -> None:
    dwolla_customer_id = DwollaCustomerAPI.create_customer(arg1)
    dwolla_wallet = DwollaFundingSourceAPI.get_wallet(dwolla_customer_id)
    DwollaCustomer.objects.create(user_id=user_id, dwolla_id=dwolla_customer_id)
    LenderWallet.objects.create(user_id=user_id, wallet_id=dwolla_wallet)