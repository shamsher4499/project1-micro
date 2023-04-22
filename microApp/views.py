from django.shortcuts import render
from django.conf import settings

def page_not_found_view(request, exception):
    base_url = settings.DEVELOPMENT_URL
    return render(request, '404.html', status=404, context={'base_url':base_url})