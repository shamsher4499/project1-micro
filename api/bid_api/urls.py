from django.urls import path
from . import views
from .views import *

urlpatterns = [
    #----------------------Lender---------------------
    path('borrowerRequest/', LenderLoansRequestAPI.as_view()),
    path('loanCalculation/', LoanCalculationAPI.as_view()),
    path('bidRequest/', BidRequestAPI.as_view()),
    path('emiCalculation/', EmiCalculator.as_view(), name='emi_calculator'),
    path('emiCalculationForWeb/', EmiCalculatorForWeb.as_view(), name='emi_calculator_for_web'),
    path('lenderBiding/', LenderBiding.as_view(), name='lender_biding'),

    #----------------------Borrower---------------------
    path('requestAmount/', BorrowerAmountRequestAPI.as_view()),
    path('contactLenderList/', ContactLenderListAPI.as_view()),
    path('loan-requirements/', BorrowerLoanLimitAPI.as_view()),


    #----------------------Common API for Borrower And Lender---------------------
    path('bid-requests/', BidRequestList.as_view(), name='bid_request_list'),
    path('biding-request-lock-procedure/', BidingRequestLockProcedure.as_view(), name='biding_request_lock_procedure'),

]