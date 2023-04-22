import json
from django.http import JsonResponse
from dwollav2.error import Error as DwollaError
from django.shortcuts import render, redirect
from django.contrib import messages
from app.decorators import *
from superadmin.models import *
from .email import *
from api.dwolla_payment import DwollaCheckBalanceAPI, DwollaTransactionHistoryAPI, DwollaFundingSourceAPI, DwollaTransferAPI
from django.core.paginator import Paginator
from api.utils import GLOBAL_PAGINATION_RECORD

@role_required
def userWallet(request):
    template_name = 'frontend/dashboard/lender/wallet.html'
    try:
        lender_wallet = LenderWallet.objects.get(user_id=request.user.id)
    except LenderWallet.DoesNotExist:
        return render(request, template_name, {'wallet':None, 'wallet_amount':None, 'page_obj':None, 'transactions':None})

    dwolla_wallet_amount = DwollaCheckBalanceAPI.get_balance(lender_wallet.wallet_id)

    wallet_transaction = DwollaCustomer.objects.get(user_id=lender_wallet.user_id)
    transactions = DwollaTransactionHistoryAPI.all_transactions(wallet_transaction.dwolla_id)
    p = Paginator(transactions, GLOBAL_PAGINATION_RECORD)
    page_number = request.GET.get('page')
    page_obj = p.get_page(page_number)

    dwolla_customer = DwollaCustomer.objects.get(user_id=request.user.id)
    dwolla_bank_accounts = DwollaFundingSourceAPI.get_all_funding(dwolla_customer.dwolla_id)
    active_bank_accounts = []
    for i in dwolla_bank_accounts:
        if i.get('type') == "bank" and i.get('removed') == False:
            active_bank_accounts.append({"id": i.get('id'), "name": i.get('name')})

    return render(request, template_name, {'wallet':lender_wallet, 'wallet_amount':dwolla_wallet_amount, 'page_obj':page_obj, 'transactions':transactions, 'active_bank_accounts': active_bank_accounts})

def check_wallet_amount_max_limit(request):
    amount = json.loads(request.body.decode()).get('amount', 0)
    amount = float(amount if amount else 0)
    wallet_limit = WalletAmountLimit.objects.all().first()
    if not amount or (wallet_limit and amount > float(wallet_limit.amount)):
        return JsonResponse({'status': False, 'message': f"You can add only max ${wallet_limit.amount} amount."})
    else:
        return JsonResponse({'status': True, 'message': f"continue"})

@role_required
def transfer_to_wallet(request):
    if request.method == 'POST':
        amount = request.POST.get('amount', 0)
        amount = float(amount if amount else 0)
        funding_source_id = request.POST.get('source')

        wallet_limit = WalletAmountLimit.objects.all().first()
        user_id = request.user.id
        if wallet_limit and amount > float(wallet_limit.amount):
            messages.error(request, f"You can add only max ${wallet_limit.amount} amount.")
            return redirect('app_lender_wallet')
        elif not DwollaCustomer.objects.filter(user_id=user_id).exists():
            messages.error(request, "Account not found.")
            return redirect('app_lender_wallet')
        elif request.user.is_verified == False:
            messages.error(request, "Please check email, your email is not verified yet.")
            return redirect('app_lender_wallet')
        elif request.user.is_active == False:
            messages.error(request, "Your Account is Inactive. Please contact the Admin.")
            return redirect('app_lender_wallet')
        
        try:
            user_wallet = LenderWallet.objects.get(user_id=user_id)
            transfer_data = {
                'amount': str(amount),
                'funding_source': funding_source_id,
                'destination_source': user_wallet.wallet_id,
                # 'destination_source': '4bc19f95-7a4e-40d3-be1d-f6ce346af2b4',
                'message':"Transfer amount"
            }
            DwollaTransferAPI.create_transfer(transfer_data)
            messages.success(request, "Amount transfer successfully.")
            return redirect('app_lender_wallet')
        except DwollaError as e:
            messages.error(request, e.body['_embedded']['errors'][0]['message'] if e.body.get('_embedded').get('errors')[0]['code'] else e.body['message'])
            return redirect('app_lender_wallet')
        except LenderWallet.DoesNotExist:
            messages.error(request, "Wallet does not exist")
            return redirect('app_lender_wallet')
        except:
            messages.error(request, "Something went wrong")
            return redirect('app_lender_wallet')


@role_required
def borrowerLoanHistory(request):
    user_id = request.user.id
    all_loans = BorrowerRequestAmount.objects.all()
    active_loans = all_loans.filter(user_id=user_id, approve=1, completed=0)
    completed_loans = all_loans.filter(user_id=user_id, approve=1, completed=1)
    data = {
        'active_loans': active_loans,
        'completed_loans': completed_loans
    }
    template_name = 'frontend/dashboard/active-loans.html'
    return render(request, template_name, data)

@role_required
def lenderLoanHistory(request):
    user_id = request.user.id
    all_loans = BorrowerRequestAmount.objects.all()
    active_loans = all_loans.filter(lender_id=user_id, approve=1, completed=0)
    completed_loans = all_loans.filter(user_id=user_id, approve=1, completed=1)
    data = {
        'active_loans': active_loans,
        'completed_loans': completed_loans
    }
    template_name = 'frontend/dashboard/active-loans.html'
    return render(request, template_name, data)

@role_required
def lendingBoxLoanHistory(request):
    user_id = request.user.id
    all_loans = BorrowerRequestAmount.objects.all()
    active_loans = all_loans.filter(user_id=user_id, approve=1, completed=0)
    completed_loans = all_loans.filter(user_id=user_id, approve=1, completed=1)
    data = {
        'active_loans': active_loans,
        'completed_loans': completed_loans
    }
    template_name = 'frontend/dashboard/active-loans.html'
    return render(request, template_name, data)


# def activeLoan(user_id):
    # template_name = 'frontend/dashboard/lender/history.html'
    # return render(request, template_name)

# @role_required
# def userDashboard(request):
#     template_name = 'frontend/dashboard/lender/dashboard.html'
#     return render(request, template_name)

# @role_required
# def userBid(request):
#     template_name = 'frontend/dashboard/lender/bid.html'
#     return render(request, template_name)