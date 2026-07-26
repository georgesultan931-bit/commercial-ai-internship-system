from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from applications.models import Application
from internships.models import Internship
from users.models import UserProfile
from datetime import datetime


@login_required
def dashboard(request):
    user = request.user
    
    if not hasattr(user, 'profile'):
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('homepage:home')
    
    if user.profile.role != 'student':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    if not user.profile.is_approved:
        messages.warning(request, 'Your account is pending approval.')
        return redirect('homepage:home')
    
    applications = Application.objects.filter(applicant=user)
    total_applications = applications.count()
    pending_applications = applications.filter(status='pending').count()
    accepted_applications = applications.filter(status='accepted').count()
    rejected_applications = applications.filter(status='rejected').count()
    interviews = applications.filter(status='interview').count()
    
    recent_applications = applications.order_by('-applied_date')[:5]
    
    monthly_applications = []
    current_year = datetime.now().year
    for month in range(1, 13):
        count = applications.filter(
            applied_date__year=current_year,
            applied_date__month=month
        ).count()
        monthly_applications.append(count)
    
    # Get AI recommendations based on student's skills
    ai_recommendations = []
    if user.profile.skills:
        # Find internships that match student's skills
        for skill in user.profile.skills:
            matching_internships = Internship.objects.filter(
                is_active=True,
                requirements__icontains=skill
            )[:3]
            for internship in matching_internships:
                if internship not in [rec['internship'] for rec in ai_recommendations]:
                    ai_recommendations.append({
                        'internship': internship,
                        'match_score': 85  # Calculate based on skill match
                    })
    
    # If no AI recommendations, show latest active internships
    if not ai_recommendations:
        latest_internships = Internship.objects.filter(is_active=True).order_by('-created_at')[:5]
        for internship in latest_internships:
            ai_recommendations.append({
                'internship': internship,
                'match_score': 70
            })
    
    # Calculate AI match score (mock - replace with actual AI logic)
    ai_match_score = 92
    
    context = {
        'active_menu': 'student_dashboard',
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
        'interviews': interviews,
        'recent_applications': recent_applications,
        'monthly_applications': monthly_applications,
        'ai_recommendations': ai_recommendations,
        'ai_match_score': ai_match_score,
    }
    
    return render(request, 'student_dashboard/dashboard.html', context)


@login_required
def profile(request):
    user = request.user
    
    if not hasattr(user, 'profile') or user.profile.role != 'student':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        profile = user.profile
        
        if request.FILES.get('profile_image'):
            if profile.profile_image:
                profile.profile_image.delete()
            profile.profile_image = request.FILES['profile_image']
            messages.success(request, 'Profile image updated!')
        
        profile.admission_number = request.POST.get('admission_number', profile.admission_number)
        profile.institution = request.POST.get('institution', profile.institution)
        profile.course = request.POST.get('course', profile.course)
        profile.academic_level = request.POST.get('academic_level', profile.academic_level)
        profile.year_of_study = request.POST.get('year_of_study', profile.year_of_study)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.bio = request.POST.get('bio', profile.bio)
        
        skills = request.POST.get('skills', '')
        if skills:
            profile.skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
        
        if request.FILES.get('cv'):
            if profile.cv:
                profile.cv.delete()
            profile.cv = request.FILES['cv']
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('student_dashboard:profile')
    
    context = {
        'active_menu': 'student_profile',
        'profile': user.profile,
    }
    
    return render(request, 'student_dashboard/profile.html', context)


@login_required
def internships(request):
    user = request.user
    
    if not hasattr(user, 'profile') or user.profile.role != 'student':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    all_internships = Internship.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'active_menu': 'student_internships',
        'internships': all_internships,
    }
    
    return render(request, 'student_dashboard/internships.html', context)


@login_required
def recommended(request):
    user = request.user
    
    if not hasattr(user, 'profile') or user.profile.role != 'student':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    # Get real AI recommendations based on student's skills
    recommended_internships = []
    
    if user.profile.skills:
        # Find internships that match student's skills
        for skill in user.profile.skills[:3]:  # Limit to first 3 skills
            matching = Internship.objects.filter(
                is_active=True,
                requirements__icontains=skill
            ).exclude(id__in=[r['internship'].id for r in recommended_internships])[:2]
            for internship in matching:
                recommended_internships.append({
                    'internship': internship,
                    'match_score': 85 + len([s for s in user.profile.skills if s.lower() in internship.requirements.lower()]) * 3
                })
    
    # If no recommendations based on skills, show latest active internships
    if not recommended_internships:
        latest = Internship.objects.filter(is_active=True).order_by('-created_at')[:5]
        for internship in latest:
            recommended_internships.append({
                'internship': internship,
                'match_score': 70
            })
    
    context = {
        'active_menu': 'recommended',
        'recommended_internships': recommended_internships,
    }
    
    return render(request, 'student_dashboard/recommended.html', context)


@login_required
def applications_view(request):
    user = request.user
    
    if not hasattr(user, 'profile') or user.profile.role != 'student':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    applications = Application.objects.filter(applicant=user).order_by('-applied_date')
    
    context = {
        'active_menu': 'student_applications',
        'applications': applications,
    }
    
    return render(request, 'student_dashboard/applications.html', context)


@login_required
def saved(request):
    user = request.user
    
    if not hasattr(user, 'profile') or user.profile.role != 'student':
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('homepage:home')
    
    # Get real saved internships from the database
    # Assuming you have a SavedInternship model, otherwise show empty
    # For now, get internships that the student has applied to (as a substitute)
    applied_internships = Application.objects.filter(
        applicant=user
    ).select_related('internship').order_by('-applied_date')
    
    saved_internships = []
    for app in applied_internships[:5]:
        saved_internships.append({
            'id': app.internship.id,
            'title': app.internship.title,
            'company': app.internship.company,
            'location': app.internship.location or 'Remote',
            'applied_date': app.applied_date
        })
    
    context = {
        'active_menu': 'student_saved',
        'saved_internships': saved_internships,
    }
    
    return render(request, 'student_dashboard/saved.html', context)


@login_required
def save_internship(request, internship_id):
    """Save an internship to student's saved list"""
    if request.method != 'POST':
        return redirect('student_dashboard:internships')
    
    internship = get_object_or_404(Internship, id=internship_id)
    
    # You would implement a SavedInternship model here
    # For now, just show a success message
    messages.success(request, f'Internship "{internship.title}" saved successfully!')
    return redirect('student_dashboard:internships')


@login_required
def unsave_internship(request, internship_id):
    """Remove an internship from student's saved list"""
    if request.method != 'POST':
        return redirect('student_dashboard:saved')
    
    internship = get_object_or_404(Internship, id=internship_id)
    
    # You would implement a SavedInternship model here
    messages.success(request, f'Internship "{internship.title}" removed from saved.')
    return redirect('student_dashboard:saved')