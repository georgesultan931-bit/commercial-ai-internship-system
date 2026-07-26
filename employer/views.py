from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from internships.models import Internship
from applications.models import Application
from users.models import UserProfile
from datetime import datetime


@login_required
def dashboard(request):
    user = request.user
    
    # Check if user has profile
    if not hasattr(user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('homepage:home')
    
    # Check if user is employer
    if user.profile.role != 'employer':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    # Check if employer is approved
    if not user.profile.is_approved:
        messages.warning(request, 'Your account is pending admin approval.')
        return redirect('homepage:home')
    
    # Get company name from profile
    company_name = user.profile.company_name
    
    # Get internships for this company
    internships = Internship.objects.filter(company=company_name) if company_name else Internship.objects.none()
    total_internships = internships.count()
    active_internships = internships.filter(is_active=True).count()
    recent_internships = internships.order_by('-created_at')[:5]
    
    # Get applications for this company's internships
    applications = Application.objects.filter(internship__in=internships)
    total_applicants = applications.count()
    pending_applications = applications.filter(status='pending').count()
    shortlisted = applications.filter(status='shortlisted').count()
    interviews_scheduled = applications.filter(status='interview').count()
    rejected_applications = applications.filter(status='rejected').count()
    accepted_applications = applications.filter(status='accepted').count()
    
    # Monthly applicants for chart
    monthly_applicants = []
    current_year = datetime.now().year
    for month in range(1, 13):
        count = applications.filter(
            applied_date__year=current_year,
            applied_date__month=month
        ).count()
        monthly_applicants.append(count)
    
    context = {
        'active_menu': 'employer_dashboard',
        'total_internships': total_internships,
        'active_internships': active_internships,
        'total_applicants': total_applicants,
        'pending_applications': pending_applications,
        'shortlisted': shortlisted,
        'interviews_scheduled': interviews_scheduled,
        'rejected_applications': rejected_applications,
        'accepted_applications': accepted_applications,
        'recent_internships': recent_internships,
        'monthly_applicants': monthly_applicants,
        'company_name': company_name,
    }
    
    return render(request, 'employer/dashboard.html', context)


@login_required
def post_internship(request):
    # Check if user is employer
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'employer':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    if not request.user.profile.is_approved:
        messages.warning(request, 'Your account is pending admin approval.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        location = request.POST.get('location')
        requirements = request.POST.get('requirements')
        deadline = request.POST.get('deadline')
        
        if not title or not description:
            messages.error(request, 'Title and description are required.')
            return redirect('employer:post_internship')
        
        company_name = request.user.profile.company_name or request.user.username
        
        internship = Internship.objects.create(
            title=title,
            description=description,
            location=location or '',
            requirements=requirements or '',
            deadline=deadline or None,
            company=company_name,
            created_by=request.user,
            is_active=True
        )
        
        messages.success(request, f'Internship "{title}" posted successfully!')
        return redirect('employer:manage_internships')
    
    return render(request, 'employer/post_internship.html')


@login_required
def manage_internships(request):
    # Check if user is employer
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'employer':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    company_name = request.user.profile.company_name
    internships = Internship.objects.filter(company=company_name) if company_name else Internship.objects.none()
    
    context = {
        'active_menu': 'manage_internships',
        'internships': internships,
    }
    
    return render(request, 'employer/manage_internships.html', context)


@login_required
def applications(request):
    # Check if user is employer
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'employer':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    company_name = request.user.profile.company_name
    internships = Internship.objects.filter(company=company_name) if company_name else Internship.objects.none()
    applications = Application.objects.filter(internship__in=internships).order_by('-applied_date')
    
    context = {
        'active_menu': 'employer_applications',
        'applications': applications,
    }
    
    return render(request, 'employer/applications.html', context)


@login_required
def company_profile(request):
    # Check if user is employer
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'employer':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        profile = request.user.profile
        profile.company_name = request.POST.get('company_name', profile.company_name)
        profile.company_email = request.POST.get('company_email', profile.company_email)
        profile.company_phone = request.POST.get('company_phone', profile.company_phone)
        profile.company_location = request.POST.get('company_location', profile.company_location)
        profile.company_description = request.POST.get('company_description', profile.company_description)
        profile.industry = request.POST.get('industry', profile.industry)
        profile.website = request.POST.get('website', profile.website)
        profile.save()
        
        messages.success(request, 'Company profile updated successfully!')
        return redirect('employer:company_profile')
    
    context = {
        'active_menu': 'company_profile',
        'profile': request.user.profile,
    }
    
    return render(request, 'employer/company_profile.html', context)


@login_required
def upload_company_logo(request):
    """Handle company logo upload"""
    if request.method == 'POST' and request.FILES.get('company_logo'):
        profile = request.user.profile
        if profile.company_logo:
            profile.company_logo.delete()
        profile.company_logo = request.FILES['company_logo']
        profile.save()
        messages.success(request, '✅ Company logo updated successfully!')
    else:
        messages.error(request, 'No image selected or invalid request.')
    
    next_url = request.POST.get('next', 'employer:company_profile')
    return redirect(next_url)


@login_required
def remove_company_logo(request):
    """Remove company logo"""
    if request.method == 'POST':
        profile = request.user.profile
        if profile.company_logo:
            profile.company_logo.delete()
            profile.save()
            messages.success(request, '✅ Company logo removed successfully!')
        else:
            messages.error(request, 'No company logo to remove.')
    
    next_url = request.POST.get('next', 'employer:company_profile')
    return redirect(next_url)