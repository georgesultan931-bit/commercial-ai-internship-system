from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models.functions import TruncMonth
from internships.models import Internship, Application, Interview
from chat.models import ChatRoom, Message, UserStatus
from users.models import UserProfile
from organizations.models import Organization
from core.utils import send_approval_email, send_rejection_email, send_admin_notification_email


@login_required(login_url='/users/login/')
def student_dashboard(request):
    """Student Dashboard"""
    user = request.user
    
    # Get user profile
    try:
        profile = user.profile
    except:
        profile = None
    
    # Get applications
    applications = Application.objects.filter(applicant=user).order_by('-applied_at')
    
    # Application statistics
    total_applications = applications.count()
    applied_count = applications.filter(status='APPLIED').count()
    reviewing_count = applications.filter(status='REVIEWING').count()
    interviewing_count = applications.filter(status='INTERVIEWING').count()
    offered_count = applications.filter(status='OFFERED').count()
    hired_count = applications.filter(status='HIRED').count()
    rejected_count = applications.filter(status='REJECTED').count()
    
    # Recent applications (last 5)
    recent_applications = applications[:5]
    
    # Recommended internships
    recommended_internships = Internship.objects.filter(
        status='APPROVED'
    ).exclude(
        id__in=applications.values_list('internship_id', flat=True)
    ).order_by('-created_at')[:5]
    
    # Saved internships
    saved_internships = []
    
    # Profile completion
    profile_completion = 0
    if profile:
        profile_completion = profile.profile_completion
    
    # Unread messages count
    unread_messages = 0
    chat_rooms = ChatRoom.objects.filter(participants=user)
    for room in chat_rooms:
        unread_messages += room.unread_count(user)
    
    # Recent chat messages
    recent_chats = []
    for room in chat_rooms.order_by('-updated_at')[:5]:
        other_user = room.participants.exclude(id=user.id).first()
        last_message = room.messages.first()
        recent_chats.append({
            'room': room,
            'other_user': other_user,
            'last_message': last_message,
        })
    
    # Get upcoming interviews
    interviews = Interview.objects.filter(
        application__applicant=user,
        status='SCHEDULED'
    ).order_by('scheduled_at')[:5]
    
    context = {
        'profile': profile,
        'total_applications': total_applications,
        'applied_count': applied_count,
        'reviewing_count': reviewing_count,
        'interviewing_count': interviewing_count,
        'offered_count': offered_count,
        'hired_count': hired_count,
        'rejected_count': rejected_count,
        'recent_applications': recent_applications,
        'recommended_internships': recommended_internships,
        'saved_internships': saved_internships,
        'profile_completion': profile_completion,
        'unread_messages': unread_messages,
        'recent_chats': recent_chats,
        'interviews': interviews,
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)


@login_required(login_url='/users/login/')
def employer_dashboard(request):
    """Employer Dashboard"""
    user = request.user
    
    # Get user profile and organization
    try:
        profile = user.profile
        organization = profile.organization
    except:
        profile = None
        organization = None
    
    if not organization:
        messages.warning(request, 'Please complete your profile and organization setup.')
        return redirect('homepage:home')
    
    # Get internships for this organization
    internships = Internship.objects.filter(organization=organization).order_by('-created_at')
    
    # Internship statistics
    total_internships = internships.count()
    active_internships = internships.filter(status='APPROVED').count()
    pending_internships = internships.filter(status='PENDING').count()
    closed_internships = internships.filter(status='CLOSED').count()
    rejected_internships = internships.filter(status='REJECTED').count()
    
    # Total applicants across all internships
    total_applicants = Application.objects.filter(internship__in=internships).count()
    
    # Recent internships
    recent_internships = internships[:5]
    
    # Recent applicants (last 5)
    recent_applicants = Application.objects.filter(
        internship__in=internships
    ).order_by('-applied_at')[:5]
    
    # Applications by status
    applications = Application.objects.filter(internship__in=internships)
    applied = applications.filter(status='APPLIED').count()
    reviewing = applications.filter(status='REVIEWING').count()
    interviewing = applications.filter(status='INTERVIEWING').count()
    offered = applications.filter(status='OFFERED').count()
    hired = applications.filter(status='HIRED').count()
    rejected = applications.filter(status='REJECTED').count()
    
    # Unread messages count
    unread_messages = 0
    chat_rooms = ChatRoom.objects.filter(participants=user)
    for room in chat_rooms:
        unread_messages += room.unread_count(user)
    
    # Recent chats
    recent_chats = []
    for room in chat_rooms.order_by('-updated_at')[:5]:
        other_user = room.participants.exclude(id=user.id).first()
        last_message = room.messages.first()
        recent_chats.append({
            'room': room,
            'other_user': other_user,
            'last_message': last_message,
        })
    
    # Get upcoming interviews
    interviews = Interview.objects.filter(
        application__internship__organization=organization,
        status='SCHEDULED'
    ).order_by('scheduled_at')[:5]
    
    context = {
        'organization': organization,
        'profile': profile,
        'total_internships': total_internships,
        'active_internships': active_internships,
        'pending_internships': pending_internships,
        'closed_internships': closed_internships,
        'rejected_internships': rejected_internships,
        'total_applicants': total_applicants,
        'recent_internships': recent_internships,
        'recent_applicants': recent_applicants,
        'applied': applied,
        'reviewing': reviewing,
        'interviewing': interviewing,
        'offered': offered,
        'hired': hired,
        'rejected': rejected,
        'unread_messages': unread_messages,
        'recent_chats': recent_chats,
        'interviews': interviews,
    }
    
    return render(request, 'dashboard/employer_dashboard.html', context)


@login_required(login_url='/users/login/')
def institution_dashboard(request):
    """Institution Dashboard"""
    user = request.user
    
    # Get user profile and organization
    try:
        profile = user.profile
        organization = profile.organization
    except:
        profile = None
        organization = None
    
    if not organization:
        messages.warning(request, 'Please complete your profile and organization setup.')
        return redirect('homepage:home')
    
    # Get students from this institution
    students = UserProfile.objects.filter(
        organization=organization,
        role='STUDENT'
    )
    
    # Student statistics
    total_students = students.count()
    verified_students = students.filter(is_verified=True).count()
    
    # Students with applications
    students_with_applications = students.filter(
        user__applications__isnull=False
    ).distinct().count()
    
    # Total internships from this institution
    internships = Internship.objects.filter(organization=organization)
    total_internships = internships.count()
    active_internships = internships.filter(status='APPROVED').count()
    
    # Recent students
    recent_students = students.order_by('-created_at')[:5]
    
    # Recent internships
    recent_internships = internships.order_by('-created_at')[:5]
    
    context = {
        'organization': organization,
        'profile': profile,
        'total_students': total_students,
        'verified_students': verified_students,
        'students_with_applications': students_with_applications,
        'total_internships': total_internships,
        'active_internships': active_internships,
        'recent_students': recent_students,
        'recent_internships': recent_internships,
    }
    
    return render(request, 'dashboard/institution_dashboard.html', context)


@login_required(login_url='/users/login/')
def admin_dashboard(request):
    """Platform Admin Dashboard"""
    user = request.user
    
    if not user.is_superuser:
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('homepage:home')
    
    # Get pending approvals
    pending_approvals = UserProfile.objects.filter(
        is_approved=False,
        is_verified=False
    ).exclude(role='STUDENT').select_related('user', 'organization')
    
    # Get all existing stats
    total_users = User.objects.count()
    total_students = UserProfile.objects.filter(role='STUDENT').count()
    total_employers = UserProfile.objects.filter(role='COMPANY_REP').count()
    total_institutions = UserProfile.objects.filter(role='UNIVERSITY_ADMIN').count()
    total_ngos = UserProfile.objects.filter(role='NGO_ADMIN').count()
    total_government = UserProfile.objects.filter(role='GOV_AGENCY').count()
    total_supervisors = UserProfile.objects.filter(role='SUPERVISOR').count()
    
    total_organizations = Organization.objects.count()
    verified_organizations = Organization.objects.filter(is_verified=True).count()
    pending_organizations = Organization.objects.filter(is_verified=False).count()
    
    total_internships = Internship.objects.count()
    pending_internships = Internship.objects.filter(status='PENDING').count()
    approved_internships = Internship.objects.filter(status='APPROVED').count()
    rejected_internships = Internship.objects.filter(status='REJECTED').count()
    closed_internships = Internship.objects.filter(status='CLOSED').count()
    
    total_applications = Application.objects.count()
    applied = Application.objects.filter(status='APPLIED').count()
    reviewing = Application.objects.filter(status='REVIEWING').count()
    interviewing = Application.objects.filter(status='INTERVIEWING').count()
    offered = Application.objects.filter(status='OFFERED').count()
    hired = Application.objects.filter(status='HIRED').count()
    rejected = Application.objects.filter(status='REJECTED').count()
    
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_internships = Internship.objects.order_by('-created_at')[:5]
    recent_applications = Application.objects.order_by('-applied_at')[:5]
    recent_organizations = Organization.objects.order_by('-created_at')[:5]
    
    total_messages = Message.objects.count()
    total_chat_rooms = ChatRoom.objects.count()
    
    # Get upcoming interviews for admin view
    upcoming_interviews = Interview.objects.filter(
        status='SCHEDULED'
    ).order_by('scheduled_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_employers': total_employers,
        'total_institutions': total_institutions,
        'total_ngos': total_ngos,
        'total_government': total_government,
        'total_supervisors': total_supervisors,
        'total_organizations': total_organizations,
        'verified_organizations': verified_organizations,
        'pending_organizations': pending_organizations,
        'total_internships': total_internships,
        'pending_internships': pending_internships,
        'approved_internships': approved_internships,
        'rejected_internships': rejected_internships,
        'closed_internships': closed_internships,
        'total_applications': total_applications,
        'applied': applied,
        'reviewing': reviewing,
        'interviewing': interviewing,
        'offered': offered,
        'hired': hired,
        'rejected': rejected,
        'recent_users': recent_users,
        'recent_internships': recent_internships,
        'recent_applications': recent_applications,
        'recent_organizations': recent_organizations,
        'total_messages': total_messages,
        'total_chat_rooms': total_chat_rooms,
        'pending_approvals': pending_approvals,
        'upcoming_interviews': upcoming_interviews,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required(login_url='/users/login/')
def approve_user(request, user_id):
    """Admin approves a user"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        profile = UserProfile.objects.get(user_id=user_id)
        
        profile.is_approved = True
        profile.is_verified = True
        profile.approved_at = timezone.now()
        profile.save()
        
        if profile.organization:
            profile.organization.is_verified = True
            profile.organization.save()
        
        send_approval_email(profile.user)
        
        return JsonResponse({
            'success': True,
            'message': f'User {profile.user.email} has been approved!'
        })
        
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required(login_url='/users/login/')
def reject_user(request, user_id):
    """Admin rejects a user"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        profile = UserProfile.objects.get(user_id=user_id)
        reason = request.POST.get('reason', 'Your registration was not approved.')
        
        send_rejection_email(profile.user, reason)
        
        user = profile.user
        profile.delete()
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'User has been rejected and removed.'
        })
        
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


# ============================================
# ADMIN MANAGEMENT VIEWS
# ============================================

@login_required(login_url='/users/login/')
def manage_organizations(request):
    """View and manage organizations"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('homepage:home')
    
    organizations = Organization.objects.all().order_by('-created_at')
    
    context = {
        'organizations': organizations,
        'total': organizations.count(),
        'verified': organizations.filter(is_verified=True).count(),
        'pending': organizations.filter(is_verified=False).count(),
    }
    
    return render(request, 'dashboard/manage_organizations.html', context)


@login_required(login_url='/users/login/')
def manage_users(request):
    """View and manage users"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('homepage:home')
    
    users = User.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
        'total': users.count(),
    }
    
    return render(request, 'dashboard/manage_users.html', context)


@login_required(login_url='/users/login/')
def platform_analytics(request):
    """View platform analytics"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('homepage:home')
    
    total_users = User.objects.count()
    total_students = UserProfile.objects.filter(role='STUDENT').count()
    total_employers = UserProfile.objects.filter(role='COMPANY_REP').count()
    total_institutions = UserProfile.objects.filter(role='UNIVERSITY_ADMIN').count()
    total_ngos = UserProfile.objects.filter(role='NGO_ADMIN').count()
    total_government = UserProfile.objects.filter(role='GOV_AGENCY').count()
    
    total_internships = Internship.objects.count()
    total_applications = Application.objects.count()
    total_organizations = Organization.objects.count()
    
    monthly_users = User.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(count=Count('id')).order_by('month')[:12]
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_employers': total_employers,
        'total_institutions': total_institutions,
        'total_ngos': total_ngos,
        'total_government': total_government,
        'total_internships': total_internships,
        'total_applications': total_applications,
        'total_organizations': total_organizations,
        'monthly_users': monthly_users,
    }
    
    return render(request, 'dashboard/platform_analytics.html', context)


@login_required(login_url='/users/login/')
def system_settings(request):
    """System settings"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('homepage:home')
    
    if request.method == 'POST':
        messages.success(request, 'Settings updated successfully!')
    
    return render(request, 'dashboard/system_settings.html')


@login_required(login_url='/users/login/')
def audit_logs(request):
    """View audit logs"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('homepage:home')
    
    context = {
        'logs': [],
    }
    
    return render(request, 'dashboard/audit_logs.html', context)