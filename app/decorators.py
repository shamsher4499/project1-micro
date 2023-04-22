from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def role_required(func):
    def check_user(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser == False:
            return func(request, *args, **kwargs)
        else:
            return redirect('home')
    return check_user
