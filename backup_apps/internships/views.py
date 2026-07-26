from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Internship, Application, Interview, Logbook
from .forms import InternshipForm, ApplicationForm  # This line is now fixed


@login_required
def post_internship(request):
    """Post a new internship"""
    try:
        profile = request.user.profile
        if not profile.organization:
            messages.error(request, 'You need to have an organization to post an internship. Please contact your organization admin.')
            return redirect('homepage:home')
        organization = profile.organization
    except:
        messages.error(request, 'Please complete your profile first.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        form = InternshipForm(request.POST, organization=organization, user=request.user)
        if form.is_valid():
            internship = form.save(commit=False)
            internship.organization = organization
            internship.posted_by = request.user
            internship.organization_email = organization.email
            internship.industry = organization.organization_type
            internship.save()
            messages.success(request, 'Internship posted successfully! It will be reviewed by an admin.')
            return redirect('internships:my_internships')
    else:
        form = InternshipForm(organization=organization, user=request.user)
    
    return render(request, 'internships/post_internship.html', {'form': form})


@login_required
def my_internships(request):
    """View internships posted by the user's organization"""
    try:
        profile = request.user.profile
        if profile.organization:
            internships = Internship.objects.filter(organization=profile.organization).order_by('-created_at')
        else:
            internships = Internship.objects.none()
    except:
        internships = Internship.objects.none()
    
    return render(request, 'internships/my_internships.html', {'internships': internships})


@login_required
def edit_internship(request, pk):
    """Edit an existing internship"""
    internship = get_object_or_404(Internship, pk=pk)
    
    try:
        if internship.organization != request.user.profile.organization:
            messages.error(request, 'You do not have permission to edit this internship.')
            return redirect('internships:my_internships')
    except:
        messages.error(request, 'Please complete your profile first.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        form = InternshipForm(request.POST, instance=internship)
        if form.is_valid():
            form.save()
            messages.success(request, 'Internship updated successfully!')
            return redirect('internships:my_internships')
    else:
        form = InternshipForm(instance=internship)
    
    return render(request, 'internships/edit_internship.html', {'form': form, 'internship': internship})


@login_required
def delete_internship(request, pk):
    """Delete an internship"""
    internship = get_object_or_404(Internship, pk=pk)
    
    try:
        if internship.organization != request.user.profile.organization:
            messages.error(request, 'You do not have permission to delete this internship.')
            return redirect('internships:my_internships')
    except:
        messages.error(request, 'Please complete your profile first.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        internship.delete()
        messages.success(request, 'Internship deleted successfully!')
        return redirect('internships:my_internships')
    
    return render(request, 'internships/delete_internship.html', {'internship': internship})


def browse_internships(request):
    """Browse all approved internships"""
    internships = Internship.objects.filter(status='APPROVED').order_by('-created_at')
    
    query = request.GET.get('q')
    category = request.GET.get('category')
    location = request.GET.get('location')
    
    if query:
        internships = internships.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(required_skills__icontains=query)
        )
    
    if category and category != 'ALL':
        internships = internships.filter(category=category)
    
    if location:
        internships = internships.filter(location__icontains=location)
    
    paginator = Paginator(internships, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'internships/browse_internships.html', {
        'page_obj': page_obj,
        'query': query,
        'category': category,
        'location': location,
    })


def internship_detail(request, pk):
    """View internship details"""
    internship = get_object_or_404(Internship, pk=pk, status='APPROVED')
    
    has_applied = False
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(
            internship=internship,
            applicant=request.user
        ).exists()
    
    return render(request, 'internships/internship_detail.html', {
        'internship': internship,
        'has_applied': has_applied,
    })


@login_required
def apply_internship(request, pk):
    """Apply to an internship"""
    internship = get_object_or_404(Internship, pk=pk, status='APPROVED')
    
    if timezone.now() > internship.application_deadline:
        messages.error(request, 'The application deadline for this internship has passed.')
        return redirect('internships:internship_detail', pk=pk)
    
    if Application.objects.filter(internship=internship, applicant=request.user).exists():
        messages.warning(request, 'You have already applied to this internship.')
        return redirect('internships:internship_detail', pk=pk)
    
    if internship.current_applicants >= internship.max_applicants:
        messages.error(request, 'This internship has reached its maximum number of applicants.')
        return redirect('internships:internship_detail', pk=pk)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.internship = internship
            application.applicant = request.user
            application.save()
            
            internship.current_applicants += 1
            internship.save()
            
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('internships:my_applications')
    else:
        form = ApplicationForm()
    
    return render(request, 'internships/apply_internship.html', {
        'form': form,
        'internship': internship,
    })


@login_required
def my_applications(request):
    """View all applications by the logged-in user"""
    applications = Application.objects.filter(
        applicant=request.user
    ).order_by('-applied_at')
    
    return render(request, 'internships/my_applications.html', {'applications': applications})


@login_required
def internship_applications(request, pk):
    """View all applications for an internship (for employers)"""
    internship = get_object_or_404(Internship, pk=pk)
    
    try:
        if internship.organization != request.user.profile.organization:
            messages.error(request, 'You do not have permission to view applications for this internship.')
            return redirect('internships:my_internships')
    except:
        messages.error(request, 'Please complete your profile first.')
        return redirect('homepage:home')
    
    applications = Application.objects.filter(
        internship=internship
    ).order_by('-applied_at')
    
    return render(request, 'internships/internship_applications.html', {
        'internship': internship,
        'applications': applications,
    })


@login_required
def update_application_status(request, pk):
    """Update application status (for employers)"""
    application = get_object_or_404(Application, pk=pk)
    
    try:
        if application.internship.organization != request.user.profile.organization:
            messages.error(request, 'You do not have permission to update this application.')
            return redirect('internships:my_internships')
    except:
        messages.error(request, 'Please complete your profile first.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Application.STATUS_CHOICES):
            application.status = status
            application.reviewed_by = request.user
            application.save()
            messages.success(request, f'Application status updated to {status}!')
    
    return redirect('internships:internship_applications', pk=application.internship.pk)


@login_required
def schedule_interview(request, application_id):
    """Schedule an interview for an application"""
    application = get_object_or_404(Application, id=application_id)
    
    try:
        if application.internship.organization != request.user.profile.organization:
            messages.error(request, 'You do not have permission to schedule interviews for this application.')
            return redirect('internships:my_internships')
    except:
        messages.error(request, 'Please complete your profile first.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        duration = request.POST.get('duration', 60)
        meeting_link = request.POST.get('meeting_link', '')
        notes = request.POST.get('notes', '')
        
        if not scheduled_at:
            messages.error(request, 'Please select a date and time.')
            return redirect('internships:schedule_interview', application_id=application_id)
        
        interview = Interview.objects.create(
            application=application,
            scheduled_at=scheduled_at,
            duration=int(duration),
            meeting_link=meeting_link,
            notes=notes,
            status='SCHEDULED'
        )
        
        application.status = 'INTERVIEWING'
        application.save()
        
        messages.success(request, f'Interview scheduled for {interview.scheduled_at.strftime("%B %d, %Y at %I:%M %p")}')
        return redirect('internships:internship_applications', pk=application.internship.pk)
    
    return render(request, 'internships/schedule_interview.html', {
        'application': application,
        'student': application.applicant,
        'internship': application.internship,
    })


@login_required
def my_interviews(request):
    """View all interviews for the logged-in user"""
    user = request.user
    
    try:
        if user.profile.role == 'STUDENT':
            interviews = Interview.objects.filter(
                application__applicant=user
            ).order_by('-scheduled_at')
        else:
            interviews = Interview.objects.filter(
                application__internship__organization=user.profile.organization
            ).order_by('-scheduled_at')
    except:
        interviews = Interview.objects.none()
    
    return render(request, 'internships/my_interviews.html', {
        'interviews': interviews,
    })


@login_required
def update_interview_status(request, interview_id):
    """Update interview status"""
    interview = get_object_or_404(Interview, id=interview_id)
    
    try:
        if interview.application.internship.organization != request.user.profile.organization:
            messages.error(request, 'You do not have permission.')
            return redirect('internships:my_interviews')
    except:
        messages.error(request, 'Permission denied.')
        return redirect('internships:my_interviews')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        feedback = request.POST.get('feedback', '')
        
        if status in dict(Interview.STATUS_CHOICES):
            interview.status = status
            if feedback:
                interview.feedback = feedback
            interview.save()
            
            if status == 'COMPLETED':
                interview.application.status = 'REVIEWING'
                interview.application.save()
            
            messages.success(request, f'Interview status updated to {status}!')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('internships:my_interviews')