from django.shortcuts import render
from django.contrib.auth.models import User
from internships.models import Internship
from applications.models import Application

def home(request):
    context = {
        'total_internships': Internship.objects.count(),
        'total_users': User.objects.count(),
        'total_applications': Application.objects.count(),
        'user': request.user,
    }
    return render(request, 'homepage/home.html', context)

def features(request):
    return render(request, 'homepage/features.html')

def pricing(request):
    return render(request, 'homepage/pricing.html')

def about(request):
    return render(request, 'homepage/about.html')

def contact(request):
    return render(request, 'homepage/contact.html')