from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def admin_only(func):
    """ The code is a decorator that only allows the function to be accessed by admins.
        The code checks if the user is authenticated and if they are superuser, 
        then it will call the function with all of its arguments and keyword arguments.
        If not, then it will redirect them back to home.
        The code will only allow the admin user to access the function.
        The permission can be changed by adding it in the decorator.
    """
    def check_user(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return func(request, *args, **kwargs)
        else:
            return redirect('home')
    return check_user