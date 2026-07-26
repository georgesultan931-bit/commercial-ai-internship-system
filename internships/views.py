from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from internships.models import Internship
from applications.models import Application
from users.models import UserProfile


def check_student_only(user):
    """Check if user is a student"""
    if not user.is_authenticated:
        return False
    if not hasattr(user, 'profile'):
        return False
    if user.profile.role != 'student':
        return False
    return True


def student_only_message(request):
    """Show polite message for non-students"""
    messages.warning(request, '📚 This section is only for students. Please login as a student to access internships.')
    return redirect('homepage:home')


@login_required
def browse_internships(request):
    if not check_student_only(request.user):
        return student_only_message(request)
    
    internships = Internship.objects.filter(is_active=True).order_by('-created_at')
    context = {
        'active_menu': 'browse_internships',
        'internships': internships,
    }
    return render(request, 'internships/browse.html', context)


@login_required
def recommended_internships(request):
    if not check_student_only(request.user):
        return student_only_message(request)
    
    # Mock AI recommendations
    recommended = [
        {'title': 'Software Engineer Intern', 'company': 'TechCorp', 'location': 'Remote', 'match_score': 95},
        {'title': 'Data Analyst Intern', 'company': 'DataFlow Labs', 'location': 'Nairobi', 'match_score': 88},
        {'title': 'ML Engineer Intern', 'company': 'AI Solutions', 'location': 'Remote', 'match_score': 82},
        {'title': 'Frontend Developer', 'company': 'WebTech', 'location': 'Kigali', 'match_score': 78},
        {'title': 'DevOps Engineer', 'company': 'CloudCo', 'location': 'Nairobi', 'match_score': 75},
    ]
    
    context = {
        'active_menu': 'recommended',
        'recommended': recommended,
    }
    return render(request, 'internships/recommended.html', context)


@login_required
def saved_internships(request):
    if not check_student_only(request.user):
        return student_only_message(request)
    
    context = {
        'active_menu': 'saved',
    }
    return render(request, 'internships/saved.html', context)


@login_required
def my_applications(request):
    if not check_student_only(request.user):
        return student_only_message(request)
    
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_date')
    context = {
        'active_menu': 'internship_applications',
        'applications': applications,
    }
    return render(request, 'internships/applications.html', context)