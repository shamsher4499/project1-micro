import stripe
from django.conf import settings
import requests
from datetime import date
import calendar
import PyPDF2
from rest_framework.parsers import FileUploadParser, MultiPartParser, JSONParser
import datetime as dt
from PIL import Image
import imagehash
from superadmin.models import *
from django.db.models import Q
from dateutil.relativedelta import relativedelta

user_type = ['BORROWER', 'LENDER', 'BOTH']
docs_type = ['pdf', 'jpg', 'jpeg', 'png', 'docs', 'xls', 'csv']
img_type = ['jpg', 'jpeg', 'png']

side_menu = {'Cashuu score':'no Url', 'Transfer Loan Request':'no Url', 'My Address':'auth/address'}


stripe.api_key = settings.STRIPE_SECRET_KEY


def get_size(file):
    return file.size <= 2*1048576


GLOBAL_PAGINATION_RECORD = 10

def get_ip():
    response = requests.get('https://api64.ipify.org?format=json').json()
    return response["ip"]

def get_location(ip_address):
    response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
    location_data = {
        "ip": ip_address,
        "city": response.get("city"),
        "region": response.get("region"),
        "country": response.get("country_name")
    }
    return location_data

def numberOfDays(y, m) -> int:
    leap = 0
    if y% 400 == 0:
        leap = 1
    elif y % 100 == 0:
        leap = 0
    elif y% 4 == 0:
        leap = 1
    if m==2:
        return 28 + leap
    list = [1,3,5,7,8,10,12]
    if m in list:
        return 31
    return 30


def calculate_extra_days_interest(start_date: str, amount: float, tenure: int) -> dict:
    """Calculates the extra days of interest and the amount of interest before the EMI.
    
    Args:
        start_date (str): The start date of the loan, in the format 'YYYY-MM-DD'.
        amount (float): The total amount of the loan.
        tenure (int): The tenure of the loan, in months.
        
    Returns:
        A dictionary containing the extra days of interest and the amount of interest before the EMI.
    """
    try:
        start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
        today = dt.datetime.today()
        days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
        per_day_interest = amount / days_in_month
        total_remaining_days = (start_date - today).days + 1
        amount_interest_before_emi = total_remaining_days * per_day_interest
        extra_days_interest = float(amount_interest_before_emi / tenure)
        return {
            'extra_days_interest': extra_days_interest,
            'amount_interest_before_emi': amount_interest_before_emi
        }
    except ValueError:
        # Handle invalid start date
        pass


# def calculate_extra_days_interest(**kwargs):
#     days = numberOfDays(int(kwargs['start_date'].split('-')[0]), int(kwargs['start_date'].split('-')[1]))
#     per_day_interest = kwargs['amount']/days
#     total_remaining_days =  int(kwargs['start_date'].split('-')[-1]) - date.today().day
#     amount_interest_before_emi = total_remaining_days*per_day_interest
#     extra_days_interest = float(amount_interest_before_emi/int(kwargs['tenure']))
#     return {
#         'extra_days_interest':extra_days_interest,
#         'amount_interest_before_emi':amount_interest_before_emi
#         }

def loan_calculator(amount:float, interest:float, month:int) -> float:
    """Calculates the monthly payment for a loan with the given amount, interest rate, and duration.
    
    Args:
        amount (float): The total amount of the loan.
        interest (float): The annual interest rate of the loan, in percent.
        month (int): The duration of the loan, in months.
        
    Returns:
        The monthly payment for the loan.
    """
    per_month = interest/12/100
    return round(amount * per_month * (1+per_month)**month / ((1+per_month)**month-1), 2)


def check_valid_pdf(file) -> bool:
    data: list = []
    # Open the PDF file
    pdf_file = PyPDF2.PdfFileReader(file)
    # Get the first page of the PDF
    page = pdf_file.getPage(0)
    # Get the text of the first page
    pdf_text = page.extractText()
    # Check if the text contains a valid tax ID
    if 'Tax ID' in pdf_text:
        return True
    else:
        return False


def check_similar_image(image_file1, image_file2):
    '''
    The code opens the two image files and calculates their hashes.
    If they are less than 30, then it returns True.
    Otherwise, it returns False.
    The code is a function that takes two image files as parameters and returns whether the two images are similar or not.
    The first parameter is an image file, which will be opened and saved as an instance of Image.
    The second parameter is an image file, which will be opened and saved as an instance of Image.
    The function begins by calculating the hash of the first image using average_hash() .
    The hash for this particular image will then be stored in a variable named "image1_hash".
    Next, the second image's hash is calculated using average_hash() .
    The hash for this particular image will then be stored in a variable named "image2_hash".
    '''
    try:
    # Open the first image file
        image1 = Image.open(image_file1)
        # Calculate the hash of the first image
        image1_hash = imagehash.average_hash(image1)
        # Open the second image file
        image2 = Image.open(image_file2)
        # Calculate the hash of the second image
        image2_hash = imagehash.average_hash(image2)
        # Compare the hash of the two images
        if image1_hash - image2_hash <= 30:
            return True
        else:
            return False
    except Exception as e:
        return False



def tier_selection(avg_amount):
    '''
    The code is trying to find the best store tier for a given amount of money.
    The code starts by filtering all the StoreTiers that have a starting price and ending price less than or equal to the average amount.
    If there is only one, it returns that object.
    Otherwise, if there are no objects in the filter, it returns None.
    The code selects the first store tier that has an ending price that is greater than or equal to the average amount.
    '''
    store_tier = StoreTier.objects.filter(Q(starting_price__lte=float(avg_amount)) & Q(end_price__gte=float(avg_amount)))
    if store_tier:
        return store_tier.first()
    else:
        return None

def check_ssn(ssn):
    ssn1 = ssn.split('-')
    ssn2 = ''
    ssn = ssn2.join(ssn1)
    if len(ssn) != 9:
        return False
    if ssn[0:3] in  ['000', '666']:
        return False
    if ssn[3:5] in  ['00']:
        return False
    if ssn[5::] in  ['0000']:
        return False
    if ssn[0] in  ['9']:
        return False
    else:
        return True

def check_ein(ssn):
    ssn1 = ssn.split('-')
    ssn2 = ''
    ssn = ssn2.join(ssn1)
    if ssn[0:2] in  ['07', '08', '09', '17', '18', '19', '28', '29', '49', '69', '70', '78', '79', '89', '96', '97']:
        return False
    else:
        return True

def check_wallet_status(user):
    try:
        user_wallet = LenderWallet.objects.get(user_id=user)
        if user_wallet.status == 'BLOCKED':
            return {
                "status": False,
                "message": "Wallet is blocked"
            }
        elif user_wallet.status == 'HOLD':
            return {
                "status": False,
                "message": "Wallet is Hold"
            }
        else:
            return {
                "status": True,
            }
    except:
        return ({
            "status": False,
            "message": "Something went wrong!"
        })

def emi_schedule(amount_data, fee, tenure, emi_start_date) -> list:
    list_data = {}
    total_amount = loan_calculator(amount_data, fee, tenure)
    extra_days_interest = calculate_extra_days_interest(start_date=emi_start_date, amount=total_amount, tenure=tenure)
    per_month_emi = float(total_amount)+extra_days_interest["extra_days_interest"]
    total_payable_amount = round(total_amount*tenure+extra_days_interest["amount_interest_before_emi"], 2)
    for i, k in enumerate(range(1, tenure+1), start=1):
        emi = {}
        month_name = (dt.datetime.strptime(emi_start_date, '%Y-%m-%d').date() + relativedelta(months=+i-1)).strftime(r"%Y-%m-%d")
        price_data = f'{format(float(total_amount)+extra_days_interest["extra_days_interest"], ".2f")}x{str(i)}={format((float(total_amount)+extra_days_interest["extra_days_interest"])*i, ".2f")}'
        emi['emi_date'] = month_name
        emi['emi_price'] = price_data
        list_data[i] = emi
    return list_data, per_month_emi, extra_days_interest, total_payable_amount


def get_days_for_edi(days) -> dict:
    divisor = 2
    value = divmod(days, 2)
    quotient = value[0]
    reminder = value[1]
    if reminder == 0:
        data = {
            '1': 1,
            '2': divisor,
            '3': quotient
        }
        # data = {
        #     '1':'Every day',
        #     '2':f'Every {divisor}nd days',
        #     '3':f'Every {quotient}th days',
        # }
        return data
    else:
        data = {
            '1': 1
        }
        return data
