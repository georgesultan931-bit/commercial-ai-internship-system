from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from users.models import UserProfile
from internships.models import Internship
from applications.models import Application
from chat.models import Notification, Announcement


def send_approval_email(user, request):
    """Send approval email to user after admin approves - Plain and simple"""
    try:
        login_link = request.build_absolute_uri('/users/login/')
        
        subject = 'Account Approved - InternHub'
        
        html_message = f'''
        <!DOCTYPE html>
        <html>
        <body>
            <p><strong>Hello {user.username},</strong></p>
            
            <p>Your account has been approved.</p>
            
            <p>You can now login:</p>
            
            <p><a href="{login_link}">{login_link}</a></p>
            
            <p><strong>Username:</strong> {user.username}<br>
            <strong>Email:</strong> {user.email}<br>
            <strong>Role:</strong> {user.profile.get_role_display}</p>
            
            <p>© InternHub</p>
        </body>
        </html>
        '''
        
        plain_message = f'''
Hello {user.username},

Your account has been approved.

You can now login:
{login_link}

Username: {user.username}
Email: {user.email}
Role: {user.profile.get_role_display}

© InternHub
        '''
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Approval email failed: {str(e)}")
        return False


@staff_member_required
def admin_dashboard(request):
    # Count users by role
    total_users = User.objects.count()
    total_students = UserProfile.objects.filter(role='student').count()
    total_employers = UserProfile.objects.filter(role='employer').count()
    total_institutions = UserProfile.objects.filter(role='institution').count()
    total_supervisors = UserProfile.objects.filter(role='supervisor').count()
    total_admins = UserProfile.objects.filter(role='admin').count()
    total_coordinators = UserProfile.objects.filter(role='coordinator').count()
    total_government = UserProfile.objects.filter(role='government').count()
    total_ngo = UserProfile.objects.filter(role='ngo').count()

    # Pending users (non-admin, not approved)
    pending_users = UserProfile.objects.filter(
        is_approved=False
    ).exclude(
        role='admin'
    ).select_related('user')

    pending_count = pending_users.count()

    total_internships = Internship.objects.count()
    active_internships = Internship.objects.filter(is_active=True).count()
    total_applications = Application.objects.count()

    context = {
        'active_menu': 'dashboard',
        'total_users': total_users,
        'total_students': total_students,
        'total_employers': total_employers,
        'total_institutions': total_institutions,
        'total_supervisors': total_supervisors,
        'total_admins': total_admins,
        'total_coordinators': total_coordinators,
        'total_government': total_government,
        'total_ngo': total_ngo,
        'pending_users': pending_users,
        'pending_count': pending_count,
        'total_internships': total_internships,
        'active_internships': active_internships,
        'total_applications': total_applications,
    }

    return render(request, 'admin_dashboard/dashboard.html', context)


@staff_member_required
def user_management(request):
    # Get all users with their profiles
    users = User.objects.select_related('profile').order_by('-date_joined')

    # Get pending users (all non-admin, not approved)
    pending_users = UserProfile.objects.filter(
        is_approved=False
    ).exclude(
        role='admin'
    ).select_related('user')

    context = {
        'active_menu': 'user_management',
        'users': users,
        'pending_users': pending_users,
        'pending_count': pending_users.count(),
    }
    return render(request, 'admin_dashboard/user_management.html', context)


@staff_member_required
def approve_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, f'User with ID {user_id} does not exist.')
        return redirect('admin_dashboard:user_management')

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(request, f'Profile for user {user.username} does not exist.')
        return redirect('admin_dashboard:user_management')

    if profile.is_approved:
        messages.warning(request, f'{user.username} is already approved.')
        return redirect('admin_dashboard:user_management')

    # Approve user
    profile.is_approved = True
    profile.approved_at = timezone.now()
    profile.approved_by = request.user
    profile.save()

    # Send approval email
    email_sent = send_approval_email(user, request)

    if email_sent:
        messages.success(request, f'✅ {user.username} has been approved! An email notification has been sent.')
    else:
        messages.success(request, f'✅ {user.username} has been approved! But email could not be sent.')

    return redirect('admin_dashboard:user_management')


@staff_member_required
def reject_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, f'User with ID {user_id} does not exist.')
        return redirect('admin_dashboard:user_management')

    username = user.username
    user.delete()
    messages.success(request, f'❌ {username} has been rejected and removed.')
    return redirect('admin_dashboard:user_management')


@staff_member_required
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        username = user.username
        user.delete()
        messages.success(request, f'🗑️ User {username} has been deleted.')
    except User.DoesNotExist:
        messages.error(request, f'User with ID {user_id} does not exist.')

    return redirect('admin_dashboard:user_management')


@staff_member_required
def toggle_user_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f'User {user.username} has been {status}.')
    except User.DoesNotExist:
        messages.error(request, f'User with ID {user_id} does not exist.')

    return redirect('admin_dashboard:user_management')


@staff_member_required
def notifications_api(request):
    pending_users = UserProfile.objects.filter(
        is_approved=False
    ).exclude(
        role='admin'
    ).select_related('user')

    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:10]

    pending_count = pending_users.count()

    notifications = []

    for profile in pending_users[:5]:
        notifications.append({
            'id': f'user_{profile.id}',
            'title': f'New {profile.role.capitalize()} Registration',
            'message': f'{profile.user.username} ({profile.user.email}) needs approval',
            'created_at': profile.created_at.strftime('%Y-%m-%d %H:%M'),
            'link': '/admin-dashboard/users/'
        })

    for notif in unread_notifications[:5]:
        notifications.append({
            'id': f'notif_{notif.id}',
            'title': notif.title,
            'message': notif.message,
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M'),
            'link': notif.link or '#'
        })

    return JsonResponse({
        'count': pending_count + unread_notifications.count(),
        'notifications': notifications[:10]
    })


@staff_member_required
def announcement_list(request):
    announcements = Announcement.objects.all().order_by('-is_pinned', '-created_at')
    context = {
        'active_menu': 'announcements',
        'announcements': announcements,
    }
    return render(request, 'admin_dashboard/announcements.html', context)


@staff_member_required
def create_announcement(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        announcement_type = request.POST.get('announcement_type', 'general')
        is_pinned = request.POST.get('is_pinned') == 'on'

        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return redirect('admin_dashboard:announcements')

        announcement = Announcement.objects.create(
            title=title,
            content=content,
            announcement_type=announcement_type,
            created_by=request.user,
            is_pinned=is_pinned,
            is_active=True
        )

        all_users = User.objects.all()
        for user in all_users:
            if user != request.user:
                Notification.objects.create(
                    recipient=user,
                    sender=request.user,
                    title=f'📢 New Announcement: {title}',
                    message=content[:200],
                    notification_type='announcement',
                    link='/announcements/'
                )

        messages.success(request, f'✅ Announcement "{title}" created!')
        return redirect('admin_dashboard:announcements')

    return redirect('admin_dashboard:announcements')


@staff_member_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)

    if request.method == 'POST':
        title = announcement.title
        announcement.delete()
        messages.success(request, f'Announcement "{title}" deleted successfully!')
        return redirect('admin_dashboard:announcements')

    return redirect('admin_dashboard:announcements')


@staff_member_required
def toggle_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)

    if request.method == 'POST':
        announcement.is_active = not announcement.is_active
        announcement.save()
        status = "activated" if announcement.is_active else "deactivated"
        messages.success(request, f'Announcement "{announcement.title}" {status}!')
        return redirect('admin_dashboard:announcements')

    return redirect('admin_dashboard:announcements')


@staff_member_required
def internship_management(request):
    internships = Internship.objects.all().order_by('-created_at')
    context = {
        'active_menu': 'internships',
        'internships': internships,
    }
    return render(request, 'admin_dashboard/internship_management.html', context)