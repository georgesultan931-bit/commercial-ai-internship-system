from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Application
from internships.models import Internship


@login_required
def application_list(request):
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_date')
    context = {
        'applications': applications,
    }
    return render(request, 'applications/list.html', context)


@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk, applicant=request.user)
    context = {
        'application': application,
    }
    return render(request, 'applications/detail.html', context)


@login_required
def apply_to_internship(request, internship_id):
    internship = get_object_or_404(Internship, pk=internship_id)
    
    # Check if already applied
    existing = Application.objects.filter(internship=internship, applicant=request.user).first()
    if existing:
        messages.warning(request, 'You have already applied for this internship.')
        return redirect('internships:internship_detail', pk=internship_id)
    
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')
        
        Application.objects.create(
            internship=internship,
            applicant=request.user,
            status='PENDING',
            cover_letter=cover_letter
        )
        
        messages.success(request, 'Application submitted successfully!')
        return redirect('applications:list')
    
    context = {
        'internship': internship,
    }
    return render(request, 'applications/apply.html', context)


@login_required
def update_application_status(request, pk):
    if request.method == 'POST':
        application = get_object_or_404(Application, pk=pk)
        
        # Check if user is the employer who posted the internship
        if application.internship.posted_by != request.user:
            messages.error(request, 'You are not authorized to update this application.')
            return redirect('employer:applications')
        
        new_status = request.POST.get('status')
        if new_status:
            application.status = new_status
            application.save()
            messages.success(request, f'Application status updated to {new_status}')
        
        return redirect('employer:applications')
    
    return redirect('employer:applications')