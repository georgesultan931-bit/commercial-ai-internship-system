from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging
import secrets
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_welcome_email(user, password=None):
    """
    Send welcome email to newly registered user
    """
    try:
        subject = 'Welcome to Commercial-Grade AI-Powered Internship Management System!'
        
        context = {
            'user': user,
            'password': password,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            'login_url': f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/users/login/",
        }
        
        html_message = render_to_string('emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        return False


def send_verification_email(user, verification_link):
    """
    Send email verification link
    """
    try:
        subject = 'Verify Your Email - Commercial-Grade AI-Powered Internship Management System'
        
        context = {
            'user': user,
            'verification_link': verification_link,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        html_message = render_to_string('emails/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def send_company_registration_email(company, admin_email):
    """
    Notify admin about new company registration
    """
    try:
        subject = f'New Company Registration: {company.name}'
        
        context = {
            'company': company,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            'admin_url': f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/admin/organizations/organization/",
        }
        
        html_message = render_to_string('emails/admin_company_registration.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Admin notification sent for {company.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
        return False


def send_contact_email(name, email, subject, message):
    """
    Send contact form email to admin
    """
    try:
        full_subject = f'Contact Form: {subject}'
        
        context = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        html_message = render_to_string('emails/contact_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            full_subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [getattr(settings, 'ADMIN_EMAIL', 'georgesultan931@gmail.com')],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Contact email sent from {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send contact email: {e}")
        return False


def send_test_email(email):
    """
    Send a test email to verify configuration
    """
    try:
        send_mail(
            'Test Email - AI Internship System',
            'This is a test email to verify your email configuration is working correctly.',
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        return False


def send_password_reset_email(user, reset_link):
    """
    Send password reset email
    """
    try:
        subject = 'Password Reset Request - Commercial-Grade AI-Powered Internship Management System'
        
        context = {
            'user': user,
            'reset_link': reset_link,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        html_message = render_to_string('emails/password_reset_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return False


def generate_verification_token():
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)


def send_student_verification_email(user):
    """
    Send verification email to student
    """
    try:
        token = generate_verification_token()
        user.profile.verification_token = token
        user.profile.save()
        
        verification_link = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/users/verify-student/{token}/"
        
        subject = 'Verify Your Email - Commercial-Grade AI-Powered Internship Management System'
        
        context = {
            'user': user,
            'verification_link': verification_link,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        html_message = render_to_string('emails/student_verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Student verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def send_admin_notification_email(user):
    """
    Send admin notification about new registration requiring approval
    """
    try:
        subject = f'New Registration Approval Required: {user.email}'
        
        context = {
            'user': user,
            'role': user.profile.role if hasattr(user, 'profile') else 'Unknown',
            'organization': user.profile.organization if hasattr(user, 'profile') else None,
            'admin_url': f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/dashboard/admin/",
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        html_message = render_to_string('emails/admin_notification_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Send to admin
        admin_emails = [getattr(settings, 'ADMIN_EMAIL', 'georgesultan931@gmail.com')]
        
        # Also send to all superusers
        from django.contrib.auth.models import User
        superusers = User.objects.filter(is_superuser=True)
        for su in superusers:
            if su.email and su.email not in admin_emails:
                admin_emails.append(su.email)
        
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Admin notification sent for {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
        return False


def send_approval_email(user):
    """
    Send approval email to user after admin approval
    """
    try:
        subject = 'Your Account Has Been Approved - Commercial-Grade AI-Powered Internship Management System'
        
        context = {
            'user': user,
            'role': user.profile.role if hasattr(user, 'profile') else 'User',
            'organization': user.profile.organization if hasattr(user, 'profile') else None,
            'login_url': f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/users/login/",
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        html_message = render_to_string('emails/approval_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Approval email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send approval email to {user.email}: {e}")
        return False


def send_rejection_email(user, reason):
    """
    Send rejection email to user
    """
    try:
        subject = 'Account Registration Update - Commercial-Grade AI-Powered Internship Management System'
        
        context = {
            'user': user,
            'reason': reason,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        html_message = render_to_string('emails/rejection_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'georgesultan931@gmail.com'),
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Rejection email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send rejection email to {user.email}: {e}")
        return False