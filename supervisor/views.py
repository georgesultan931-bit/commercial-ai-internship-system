from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from users.models import UserProfile
from .models import SupervisorProfile, StudentAssignment


@login_required
def dashboard(request):
    """Supervisor Dashboard"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        profile = UserProfile.objects.get(user=request.user)
        assigned_students = supervisor.assigned_students.all()
        
        context = {
            'supervisor': supervisor,
            'is_approved': profile.is_approved,
            'assigned_count': assigned_students.count(),
            'active_count': supervisor.assignments.filter(status='active').count(),
            'pending_count': supervisor.assignments.filter(status='pending').count(),
            'completed_count': supervisor.assignments.filter(status='completed').count(),
            'assigned_students': assigned_students,
        }
        return render(request, 'supervisor/dashboard.html', context)
    
    except SupervisorProfile.DoesNotExist:
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role == 'supervisor':
                supervisor = SupervisorProfile.objects.create(
                    user=request.user,
                    supervisor_id=f'SUP{request.user.id:04d}',
                    is_verified=True,
                    is_active=True
                )
                messages.success(request, 'Supervisor profile created!')
                return redirect('supervisor:dashboard')
            else:
                messages.error(request, 'You are not registered as a supervisor.')
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('homepage:home')
    
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('homepage:home')


@login_required
def profile(request):
    """Supervisor Profile"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        context = {
            'supervisor': supervisor,
        }
        return render(request, 'supervisor/profile.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')


@login_required
def assigned_students(request):
    """View assigned students"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        students = supervisor.assigned_students.all()
        
        context = {
            'supervisor': supervisor,
            'students': students,
        }
        return render(request, 'supervisor/assigned_students.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')


@login_required
def student_detail(request, student_id):
    """View student details"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        student = get_object_or_404(UserProfile, id=student_id, role='student')
        
        if student not in supervisor.assigned_students.all():
            messages.error(request, 'You are not assigned to this student.')
            return redirect('supervisor:assigned_students')
        
        context = {
            'supervisor': supervisor,
            'student': student,
        }
        return render(request, 'supervisor/student_detail.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')


@login_required
def internship_monitoring(request):
    """Monitor student internships"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        assignments = supervisor.assignments.all()
        
        context = {
            'supervisor': supervisor,
            'assignments': assignments,
        }
        return render(request, 'supervisor/internship_monitoring.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')


@login_required
def logbooks(request):
    """View student logbooks"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        assigned_students = supervisor.assigned_students.all()
        
        context = {
            'supervisor': supervisor,
            'assigned_students': assigned_students,
        }
        return render(request, 'supervisor/logbooks.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')


@login_required
def evaluations(request):
    """Student evaluations"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        assigned_students = supervisor.assigned_students.all()
        
        context = {
            'supervisor': supervisor,
            'assigned_students': assigned_students,
            'total_evaluations': 0,
            'pending_evaluations': 0,
            'completed_evaluations': 0,
        }
        return render(request, 'supervisor/evaluations.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')


@login_required
def reports(request):
    """Generate reports"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        assigned_students = supervisor.assigned_students.all()
        active_count = supervisor.assignments.filter(status='active').count()
        pending_count = supervisor.assignments.filter(status='pending').count()
        completed_count = supervisor.assignments.filter(status='completed').count()
        
        # Calculate completion rate
        total = active_count + pending_count + completed_count
        if total > 0:
            completion_rate = f"{int((completed_count / total) * 100)}%"
        else:
            completion_rate = "0%"
        
        context = {
            'supervisor': supervisor,
            'assigned_students': assigned_students,
            'active_count': active_count,
            'pending_count': pending_count,
            'completed_count': completed_count,
            'total_reports': 0,
            'completion_rate': completion_rate,
        }
        return render(request, 'supervisor/reports.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')


@login_required
def messages_view(request):
    """View messages"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        assigned_students = supervisor.assigned_students.all()
        
        context = {
            'supervisor': supervisor,
            'assigned_students': assigned_students,
        }
        return render(request, 'supervisor/messages.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')


@login_required
def settings(request):
    """Supervisor settings"""
    try:
        supervisor = SupervisorProfile.objects.get(user=request.user)
        
        if request.method == 'POST':
            supervisor.phone = request.POST.get('phone', supervisor.phone)
            supervisor.office_location = request.POST.get('office_location', supervisor.office_location)
            supervisor.office_hours = request.POST.get('office_hours', supervisor.office_hours)
            supervisor.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('supervisor:settings')
        
        context = {
            'supervisor': supervisor,
        }
        return render(request, 'supervisor/settings.html', context)
    except SupervisorProfile.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('homepage:home')