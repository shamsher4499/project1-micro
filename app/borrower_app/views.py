from api.utils import GLOBAL_PAGINATION_RECORD
from django.core.paginator import Paginator
from api.utils import check_ssn
from superadmin.models import DwollaCustomer
import json
from plaid_api.utils import ItemToken
from dwollav2.error import Error as DwollaError
from api.dwolla_payment import DwollaCustomerAPI, DwollaFundingSourceAPI
from django.shortcuts import render, redirect
from django.contrib import messages
from app.decorators import *
from superadmin.models import *
from .email import *
from django.db.models import Avg

@role_required
def borrowerDashboard(request):
    template_name = 'frontend/dashboard/dashboard.html'
    if request.method=="POST":
        data = request.POST
        request_type = request.POST.get('request_type')
        amount = request.POST.get('amount')
        fee = request.POST.get('fee')
        tenure = request.POST.get('tenure')
        if request_type not in ['DIRECT', 'BID']:
            messages.error(request, "Please select request type.")
            return render(request, template_name, {'data':data})
        if amount.isspace() or amount == '':
            messages.error(request, "Price can't be blank.")
            return render(request, template_name, {'data':data})
        if fee.isspace() or fee == '':
            messages.error(request, "Fee can't be blank.")
            return render(request, template_name, {'data':data})
        if tenure.isspace() or tenure == '':
            messages.error(request, "Tenure can't be blank.")
            return render(request, template_name, {'data':data})
        
    store_profiles = StoreProfile.objects.all()
    borrowers_request = BorrowerRequestAmount.objects.filter(lender_id=request.user.id, approve=False, completed=False, reject=False).order_by('-id')
    loan_management = LoanManagement.objects.first()

    p = Paginator(store_profiles, GLOBAL_PAGINATION_RECORD)
    page_number = request.GET.get('page')
    page_obj = p.get_page(page_number) 
   

    return render(request, template_name, {'lending_boxes': page_obj, 'borrowers_request':borrowers_request, 'loan_management': loan_management})

@role_required
def createBidRequest(request):
    if request.method == 'POST':
        user_data = request.user
        amount = request.POST.get('amount')
        fee = request.POST.get('fee')
        tenure = request.POST.get('tenure')
        request_type = request.POST.get('request_type')

        loan_management = LoanManagement.objects.first()
        if (loan_management and float(amount) > float(loan_management.amount)) or not float(amount) >= 100:
            messages.error(request, f"Amount must be valid or greater than $100 and less than ${loan_management.amount}.")
            return redirect('app_dashboard')
        elif (loan_management and float(fee) > float(loan_management.interest)) or not float(fee) > 0:
            messages.error(request, f"Fee must be greater than 1 and less than {loan_management.interest}.")
            return redirect('app_dashboard')
        elif not int(tenure) >= 1 and int(tenure) <= loan_management.tenure_month:
            messages.error(request, f"Tenure must be between 1 to {loan_management.tenure_month} months.")
            return redirect('app_dashboard')
        elif not LenderWallet.objects.filter(user_id=user_data.id).exists():
            messages.error(request, "Please setup account first.")
            return redirect('app_dashboard')
        
        # if request_type == 'DIRECT':
        #     if BorrowerRequestAmount.objects.filter(user_id=user_data.id, approve=0, reject=0).exists():
        #         messages.error(request, "Your Request is already pending.")
        #         return redirect('app_dashboard')
            
        #     request_sent = False
        #     for i in json.loads(data['lenderList']):
        #         if i != user_data.id:
        #             if LenderWallet.objects.filter(user_id=i).exists():
        #                 if not BorrowerRequestAmount.objects.filter(user_id=user_data.id, lender_id=i, approve=0).exists():
        #                     BorrowerRequestAmount.objects.create(user_id=user_data.id, amount=data['amount'], 
        #                     request_type=data['request_type'], fee=data['fee'], tenure=data['tenure'], lender_id=i)
        #                     request_sent = True
        #     if request_sent:
        #         return Response({
        #             "status": True,
        #             'message': "Request Raised.",
        #         })   
        #     else:
        #         return Response({
        #             "status": False,
        #             'message': "Please setup account first.",
        #         })

        if request_type == 'BID':
            if BorrowerRequestAmount.objects.filter(user_id=user_data.id, approve=0).exists():
                messages.error(request, "Your Request is already pending.")
                return redirect('app_dashboard')
            
            all_lenders = User.objects.filter(is_superuser=False, is_active=True, is_verified=True).exclude(id=user_data.id)
            lender_wallet_ids = LenderWallet.objects.filter(user_id__in=all_lenders).values_list('user_id', flat=True)
            borrower_request_amount_list = []
            for i in lender_wallet_ids:
                borrower_request_amount_list.append(BorrowerRequestAmount(user_id=user_data.id, amount=amount, request_type=request_type, fee=fee, tenure=tenure, lender_id=i))
            BorrowerRequestAmount.objects.bulk_create(borrower_request_amount_list)
            messages.success(request, "Request Raised.")
            return redirect('app_dashboard')
        
    return redirect('app_dashboard')

@role_required
def rejectBidRequest(request, slug):
    BorrowerRequestAmount.objects.get(slug=slug).delete()
    messages.success(request, "Request Rejected")
    return redirect('app_bid_request')

@role_required
def usercashuuScore(request):
    template_name = 'frontend/dashboard/cashu-score.html'
    return render(request, template_name)

@role_required
def userbid(request):
    user_id = request.user.id
    template_name = 'frontend/dashboard/bid-request.html'
    all_request = BorrowerRequestAmount.objects.all().filter(request_type='BID')
    borrower_request = all_request.filter(user_id=user_id, approve=False, completed=False, reject=False).order_by('-id')
    lender_request = all_request.filter(lender_id=user_id, approve=False, completed=False, reject=False).order_by('-id')
    context = {
        'borrower_request':borrower_request,
        'lender_request':lender_request
    }
    return render(request, template_name, context)

# @role_required
# def userLoanHistory(request):
#     print('---------------')
#     template_name = 'frontend/dashboard/active-loans.html'
#     return render(request, template_name)


@role_required
def userWallet(request):
    template_name = 'frontend/dashboard/lender/wallet.html'
    return render(request, template_name)

@role_required
def lendingBoxDetail(request, store_profile_slug):
    template_name = 'frontend/lender-box/detail.html'
    user_id = request.user.id
    try:
        lending_box = StoreProfile.objects.get(slug=store_profile_slug)
        store_id = lending_box.user_id
        store_reviews = StoreRating.objects.filter(store_id=store_id)
        is_user_rated = store_reviews.filter(user_id=user_id).exists()
    except StoreProfile.DoesNotExist:
        messages.error(request, "Lending box not found")
        return redirect('app_dashboard')

    if request.method == "POST":
        rating = request.POST.get('rate')
        review = request.POST.get('review')
        if is_user_rated:
            messages.error(request, "You already provided your review")
            return redirect('app_lending_box_detail', store_profile_slug)
        elif not review:
            messages.error(request, "Please Provide Review")
            return redirect('app_lending_box_detail', store_profile_slug)

        StoreRating.objects.get_or_create(user_id=user_id, store_id=store_id, rating=rating, review=review)
        store_avg_rating = store_reviews.aggregate(avg_rating = Avg('rating'))
        lending_box.rating = store_avg_rating.get('avg_rating')
        lending_box.save()

    return render(request, template_name, {'lending_box': lending_box, 'store_reviews': store_reviews, 'is_user_rated': is_user_rated})

@role_required
def createDwollaAccount(request):
    template_name = "frontend/dashboard/create-dwolla-account.html"
    if request.method == "POST":
        try:
            customer = {
                'firstName': request.POST.get('first_name', None),
                'lastName': request.POST.get('last_name', None),
                'email': request.POST.get('email', None),
                "address1": request.POST.get('address', ''),
                "city": request.POST.get('city', '').upper(),
                "state": request.POST.get('state', ''),
                "postalCode": request.POST.get('postal_code', ''),
                "dateOfBirth": request.POST.get('date_of_birth', ''),
                "ssn": request.POST.get('ssn', ''),
            }
            if not check_ssn(customer.get('ssn')):
                messages.error(request, "Please Enter Valid SSN")
                return redirect('create_dwolla_account')
                # return render(request, template_name, {'customer': customer})
            
            dwolla_customer = DwollaCustomerAPI.create_customer(customer)
            dwolla_wallet = DwollaFundingSourceAPI.get_wallet(dwolla_customer)
            user_id = request.user.id
            DwollaCustomer.objects.create(user_id=user_id, dwolla_id=dwolla_customer)
            LenderWallet.objects.create(user_id=user_id, wallet_id=dwolla_wallet)
            messages.success(request, "Dwolla Account Created Successfully")
            return redirect('user_accounts')
        except DwollaError as e:
            messages.error(request, e.body['_embedded']['errors'][0]['message'])
            return redirect('create_dwolla_account')
        # except:
        #     messages.error(request, "Something went wrong")
        #     return redirect('create_dwolla_account')
    return render(request, template_name)

@role_required
def userAccounts(request):
    template_name = 'frontend/dashboard/my-account.html'
    # is_user_have_dwolla_account = DwollaCustomer.objects.filter(user_id=user_id).exists()
    # if is_user_have_dwolla_account:
    # else:
    #     return redirect('create_dwolla_account')
    try:
        user_id = request.user.id
        dwolla_customer = DwollaCustomer.objects.get(user_id=user_id)
        plaid_link_token = json.loads(ItemToken.create_link_token()).get('link_token')
        dwolla_bank_accounts = DwollaFundingSourceAPI.get_all_funding(dwolla_customer.dwolla_id)
        active_bank_accounts = []
        for i in dwolla_bank_accounts:
            if i.get('type') == "bank" and i.get('removed') == False:
                active_bank_accounts.append({"id": i.get('id'), "name": i.get('name'), "status": i.get('status')})
        
        return render(request, template_name, {'plaid_link_token': plaid_link_token, 'active_bank_accounts': active_bank_accounts})
    except DwollaCustomer.DoesNotExist:
        messages.error(request, "Dwolla account is not created yet")
    
def deletePlaidAccount(request, funding_source_id):
    DwollaFundingSourceAPI.remove_funding(funding_source_id)
    messages.error(request, "account deleted successfully")
    return redirect('user_accounts')