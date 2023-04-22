from django.shortcuts import render, redirect
from django.contrib import messages
from app.decorators import *
from superadmin.models import *
from .email import *

@role_required
def userWallet(request):
    template_name = 'frontend/dashboard/lender/wallet.html'
    return render(request, template_name)

@role_required
def userHistory(request):
    template_name = 'frontend/dashboard/lender/history.html'
    return render(request, template_name)

@role_required
def userDashboard(request):
    template_name = 'frontend/dashboard/lender/dashboard.html'
    return render(request, template_name)

@role_required
def lenderBid(request):
    template_name = 'frontend/dashboard/lender/bid.html'
    return render(request, template_name)