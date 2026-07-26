from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
import secrets
from users.models import UserProfile


def generate_verification_token():
    return secrets.token_urlsafe(32)


def send_verification_email(user, request):
    """Send verification email with plain clickable link"""
    try:
        token = generate_verification_token()
        
        if hasattr(user, 'profile'):
            user.profile.verification_token = token
            user.profile.save()
        
        verification_link = request.build_absolute_uri(
            f'/users/verify-email/{token}/'
        )
        
        subject = 'Verify Your Email - InternHub'
        
        html_message = f'''
        <!DOCTYPE html>
        <html>
        <body>
            <p><strong>Hello {user.username},</strong></p>
            
            <p>Thank you for registering. Please verify your email:</p>
            
            <p><a href="{verification_link}">{verification_link}</a></p>
            
            <p>This link expires in 24 hours.</p>
            
            <p>If you didn't create an account, please ignore this email.</p>
            
            <p>© InternHub</p>
        </body>
        </html>
        '''
        
        plain_message = f'''
Hello {user.username},

Thank you for registering. Please verify your email:
{verification_link}

This link expires in 24 hours.

If you didn't create an account, please ignore this email.

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
        print(f"Email sending failed: {str(e)}")
        return False


def send_pending_approval_email(user, request):
    """Send email to users informing them they are pending approval - Plain and simple"""
    try:
        subject = 'Account Pending Approval - InternHub'
        
        role_display = user.profile.get_role_display()
        
        html_message = f'''
        <!DOCTYPE html>
        <html>
        <body>
            <p><strong>Hello {user.username},</strong></p>
            
            <p>Thank you for registering as a {role_display}.</p>
            
            <p>Your account is pending admin approval.</p>
            
            <p>You will receive a confirmation email once approved.</p>
            
            <p>This process usually takes 24-48 hours.</p>
            
            <p>© InternHub</p>
        </body>
        </html>
        '''
        
        plain_message = f'''
Hello {user.username},

Thank you for registering as a {role_display}.

Your account is pending admin approval.

You will receive a confirmation email once approved.

This process usually takes 24-48 hours.

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
        print(f"Pending approval email failed: {str(e)}")
        return False


def send_admin_approval_notification(user, request):
    """Send notification to admin about new user waiting for approval"""
    try:
        admin_users = User.objects.filter(is_staff=True)
        
        for admin in admin_users:
            if admin.email:
                admin_link = request.build_absolute_uri('/admin-dashboard/users/')
                
                subject = f'New User Registration - {user.username}'
                
                html_message = f'''
                <!DOCTYPE html>
                <html>
                <body>
                    <p><strong>New User Registration</strong></p>
                    
                    <p>A new user has registered and needs your approval.</p>
                    
                    <p><strong>Username:</strong> {user.username}<br>
                    <strong>Email:</strong> {user.email}<br>
                    <strong>Role:</strong> {user.profile.get_role_display}<br>
                    <strong>Registered:</strong> {user.date_joined|date:"Y-m-d H:i"}</p>
                    
                    <p><a href="{admin_link}">Review User</a></p>
                    
                    <p>© InternHub - Commercial-Grade AI-Powered Internship System</p>
                </body>
                </html>
                '''
                
                plain_message = f'''
New User Registration

A new user has registered and needs your approval.

Username: {user.username}
Email: {user.email}
Role: {user.profile.get_role_display}
Registered: {user.date_joined.strftime('%Y-%m-%d %H:%M')}

Review user: {admin_link}

© InternHub - Commercial-Grade AI-Powered Internship System
                '''
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    html_message=html_message,
                    fail_silently=False,
                )
        return True
    except Exception as e:
        print(f"Admin notification failed: {str(e)}")
        return False


def is_profile_complete(user):
    """Check if user profile is complete based on role"""
    if not hasattr(user, 'profile'):
        return False
    
    profile = user.profile
    
    if profile.role == 'student':
        required_fields = [
            profile.admission_number,
            profile.institution,
            profile.course,
            profile.academic_level,
            profile.year_of_study,
            profile.phone,
            profile.skills,
        ]
    elif profile.role == 'employer':
        required_fields = [
            profile.company_name,
            profile.industry,
            profile.company_email,
            profile.company_phone,
            profile.company_location,
            profile.company_description,
        ]
    elif profile.role == 'supervisor':
        required_fields = [
            profile.full_name,
            profile.staff_id,
            profile.department,
            profile.position,
            profile.supervisor_phone,
            profile.supervisor_institution,
        ]
    elif profile.role == 'institution':
        required_fields = [
            profile.institution_name,
            profile.institution_type,
            profile.institution_email,
            profile.institution_phone,
            profile.county,
        ]
    else:
        required_fields = [
            profile.phone,
            profile.location,
        ]
    
    for field in required_fields:
        if not field:
            return False
    
    return True


def login_view(request):
    if request.user.is_authenticated:
        # Check if user is approved
        if hasattr(request.user, 'profile'):
            if not request.user.profile.is_approved and request.user.profile.role != 'admin':
                messages.warning(request, 'Your account is pending admin approval.')
                return redirect('users:pending_approval')
        
        if not is_profile_complete(request.user):
            return redirect('users:complete_profile')
        
        if hasattr(request.user, 'profile'):
            if request.user.is_staff or request.user.profile.role == 'admin':
                return redirect('admin_dashboard:dashboard')
            elif request.user.profile.role == 'student':
                return redirect('student_dashboard:dashboard')
            elif request.user.profile.role == 'employer':
                return redirect('employer:dashboard')
            elif request.user.profile.role == 'supervisor':
                return redirect('supervisor:dashboard')
            elif request.user.profile.role == 'institution':
                return redirect('institution:dashboard')
        return redirect('homepage:home')

    if request.method == 'POST':
        login_input = request.POST.get('username')  # Can be username or email
        password = request.POST.get('password')

        if not login_input or not password:
            messages.error(request, 'Please enter both username/email and password.')
            return redirect('users:login')

        # Try to find user by email first
        try:
            user_obj = User.objects.get(email=login_input)
            username = user_obj.username
        except User.DoesNotExist:
            # If not found by email, use as username
            username = login_input

        # Authenticate with username and password
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if email is verified
            if hasattr(user, 'profile') and not user.profile.email_verified:
                messages.error(request, 'Please verify your email first. Check your inbox for the verification link.')
                return redirect('users:login')

            # Check if user is active
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
                return redirect('users:login')

            # CHECK APPROVAL - Students and Admin are approved, others need approval
            if hasattr(user, 'profile'):
                if not user.profile.is_approved and user.profile.role != 'admin' and user.profile.role != 'student':
                    messages.warning(
                        request,
                        'Your account is awaiting administrator approval. '
                        'You will receive an email once your account has been approved.'
                    )
                    return redirect('users:pending_approval')

            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            if not hasattr(user, 'profile'):
                if user.is_superuser or user.is_staff:
                    role = 'admin'
                    is_approved = True
                else:
                    role = 'student'
                    is_approved = True

                UserProfile.objects.create(
                    user=user,
                    role=role,
                    is_approved=is_approved,
                    email_verified=is_approved
                )
                messages.warning(request, 'Profile was missing. A new profile has been created.')

            if not is_profile_complete(user):
                messages.info(request, 'Please complete your profile to access the dashboard.')
                return redirect('users:complete_profile')

            if hasattr(user, 'profile'):
                if user.is_staff or user.profile.role == 'admin':
                    return redirect('admin_dashboard:dashboard')
                elif user.profile.role == 'student':
                    return redirect('student_dashboard:dashboard')
                elif user.profile.role == 'employer':
                    return redirect('employer:dashboard')
                elif user.profile.role == 'supervisor':
                    return redirect('supervisor:dashboard')
                elif user.profile.role == 'institution':
                    return redirect('institution:dashboard')
                else:
                    return redirect('homepage:home')
            else:
                return redirect('homepage:home')
        else:
            # Check if user exists
            if User.objects.filter(username=username).exists() or User.objects.filter(email=login_input).exists():
                messages.error(request, 'Invalid password. Please try again.')
            else:
                messages.error(request, 'Username or email does not exist. Please sign up first.')
            return redirect('users:login')

    return render(request, 'users/login.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'student')

        if not username or not email or not password or not password2:
            messages.error(request, 'All fields are required.')
            return redirect('users:signup')

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('users:signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('users:signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('users:signup')

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        user.is_active = False
        user.save()

        # Students are auto-approved, others need admin approval
        is_approved = True if role == 'student' else False
        email_verified = False

        # Get the profile created by the signal and update it
        profile = user.profile

        profile.role = role
        profile.is_approved = is_approved
        profile.email_verified = email_verified
        profile.verification_token = generate_verification_token()

        profile.save()

        # Send verification email
        email_sent = send_verification_email(user, request)

        if email_sent:
            messages.success(request, 'Account created! Please check your email to verify your account.')
        else:
            messages.warning(request, 'Account created! But we could not send verification email.')

        # Send pending approval email to non-students
        if role != 'student':
            send_pending_approval_email(user, request)
            messages.info(request, f'Your {role} registration is pending admin approval. You will be notified once approved.')
            send_admin_approval_notification(user, request)
        else:
            messages.success(request, 'Your student account has been auto-approved! Please verify your email and login.')

        return redirect('users:login')

    return render(request, 'users/signup.html')


def verify_email(request, token):
    """Verify user's email and redirect based on role"""
    try:
        profile = UserProfile.objects.get(verification_token=token)
        user = profile.user
        
        if user.date_joined:
            time_diff = timezone.now() - user.date_joined
            if time_diff.total_seconds() > 86400:
                messages.error(request, 'Verification link has expired. Please request a new one.')
                return redirect('users:login')
        
        profile.email_verified = True
        profile.verification_token = None
        profile.verified_at = timezone.now()
        profile.save()
        
        user.is_active = True
        user.save()
        
        messages.success(request, '✅ Email verified successfully!')
        
        # Redirect based on role
        if profile.role == 'student':
            # Students are auto-approved
            profile.is_approved = True
            profile.save()
            messages.success(request, 'Your account has been approved! Please login.')
            return redirect('users:login')
        else:
            # Non-students need admin approval
            messages.info(request, 'Your account is now pending admin approval. You will be notified once approved.')
            return redirect('users:pending_approval')
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link. Please contact support.')
        return redirect('users:login')


@login_required
def complete_profile(request):
    profile = request.user.profile
    
    if not profile.is_approved and profile.role != 'admin' and profile.role != 'student':
        messages.warning(request, 'Your account is pending admin approval. Please wait for approval before completing your profile.')
        return redirect('users:pending_approval')
    
    if is_profile_complete(request.user):
        messages.info(request, 'Your profile is already complete.')
        return redirect_to_dashboard(request.user)
    
    if request.method == 'POST':
        role = profile.role
        
        # ============================================================
        # STUDENT PROFILE FIELDS
        # ============================================================
        if role == 'student':
            profile.admission_number = request.POST.get('admission_number')
            profile.institution = request.POST.get('institution')
            profile.course = request.POST.get('course')
            profile.academic_level = request.POST.get('academic_level')
            profile.year_of_study = int(request.POST.get('year_of_study', 1))
            profile.phone = request.POST.get('phone')
            
            skills = request.POST.get('skills', '')
            if skills:
                profile.skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
            
            if request.FILES.get('cv'):
                if profile.cv:
                    profile.cv.delete()
                profile.cv = request.FILES['cv']
        
        # ============================================================
        # EMPLOYER PROFILE FIELDS
        # ============================================================
        elif role == 'employer':
            profile.company_name = request.POST.get('company_name')
            profile.industry = request.POST.get('industry')
            profile.company_email = request.POST.get('company_email')
            profile.company_phone = request.POST.get('company_phone')
            profile.company_location = request.POST.get('company_location')
            profile.company_description = request.POST.get('company_description')
            profile.website = request.POST.get('website')
            
            if request.FILES.get('company_logo'):
                if profile.company_logo:
                    profile.company_logo.delete()
                profile.company_logo = request.FILES['company_logo']
        
        # ============================================================
        # INSTITUTION PROFILE FIELDS
        # ============================================================
        elif role == 'institution':
            profile.institution_name = request.POST.get('institution_name')
            profile.institution_type = request.POST.get('institution_type')
            profile.institution_email = request.POST.get('institution_email')
            profile.institution_phone = request.POST.get('institution_phone')
            profile.county = request.POST.get('county')
            profile.address = request.POST.get('address')
            
            if request.FILES.get('logo'):
                if profile.logo:
                    profile.logo.delete()
                profile.logo = request.FILES['logo']
        
        # ============================================================
        # SUPERVISOR PROFILE FIELDS
        # ============================================================
        elif role == 'supervisor':
            profile.full_name = request.POST.get('full_name')
            profile.staff_id = request.POST.get('staff_id')
            profile.department = request.POST.get('department')
            profile.position = request.POST.get('position')
            profile.supervisor_phone = request.POST.get('supervisor_phone')
            profile.supervisor_institution = request.POST.get('supervisor_institution')
            profile.office_location = request.POST.get('office_location')
            
            if request.FILES.get('supervisor_photo'):
                if profile.supervisor_photo:
                    profile.supervisor_photo.delete()
                profile.supervisor_photo = request.FILES['supervisor_photo']
        
        # Calculate profile completion
        profile.calculate_completion()
        profile.save()
        
        messages.success(request, '✅ Profile completed successfully!')
        return redirect_to_dashboard(request.user)
    
    context = {
        'profile': profile,
        'role': profile.role,
        'academic_levels': profile.ACADEMIC_LEVEL_CHOICES if hasattr(profile, 'ACADEMIC_LEVEL_CHOICES') else [],
        'institution_types': profile.INSTITUTION_TYPE_CHOICES if hasattr(profile, 'INSTITUTION_TYPE_CHOICES') else [],
    }
    
    return render(request, 'users/complete_profile.html', context)


@login_required
def upload_profile_image(request):
    """Handle profile image upload"""
    if request.method == 'POST' and request.FILES.get('profile_image'):
        profile = request.user.profile
        if profile.profile_image:
            profile.profile_image.delete()
        profile.profile_image = request.FILES['profile_image']
        profile.save()
        messages.success(request, '✅ Profile image updated successfully!')
    else:
        messages.error(request, 'No image selected or invalid request.')
    
    next_url = request.POST.get('next', 'homepage:home')
    return redirect(next_url)


@login_required
def remove_profile_image(request):
    """Remove profile image"""
    if request.method == 'POST':
        profile = request.user.profile
        if profile.profile_image:
            profile.profile_image.delete()
            profile.save()
            messages.success(request, '✅ Profile image removed successfully!')
        else:
            messages.error(request, 'No profile image to remove.')
    
    next_url = request.POST.get('next', 'homepage:home')
    return redirect(next_url)


def redirect_to_dashboard(user):
    """Helper function to redirect user to their dashboard"""
    if hasattr(user, 'profile'):
        if user.is_staff or user.profile.role == 'admin':
            return redirect('admin_dashboard:dashboard')
        elif user.profile.role == 'student':
            return redirect('student_dashboard:dashboard')
        elif user.profile.role == 'employer':
            return redirect('employer:dashboard')
        elif user.profile.role == 'supervisor':
            return redirect('supervisor:dashboard')
        elif user.profile.role == 'institution':
            return redirect('institution:dashboard')
    return redirect('homepage:home')


def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            if hasattr(user, 'profile'):
                if user.profile.email_verified:
                    messages.info(request, 'Your email is already verified. Please login.')
                    return redirect('users:login')
                
                token = generate_verification_token()
                user.profile.verification_token = token
                user.profile.save()
                
                send_verification_email(user, request)
                messages.success(request, 'Verification email has been resent. Please check your inbox.')
                return redirect('users:login')
            else:
                messages.error(request, 'User profile not found. Please contact support.')
                
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
            
        return redirect('users:login')
    
    return render(request, 'users/resend_verification.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('homepage:home')


def profile_view(request):
    """View for users to see their profile"""
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to view your profile.')
        return redirect('users:login')
    
    # Check if user is approved
    if hasattr(request.user, 'profile'):
        if not request.user.profile.is_approved and request.user.profile.role != 'admin' and request.user.profile.role != 'student':
            messages.warning(request, 'Your account is pending admin approval.')
            return redirect('users:pending_approval')
    
    context = {
        'profile': request.user.profile,
        'user': request.user,
    }
    return render(request, 'users/profile.html', context)


def choose_registration(request):
    return render(request, 'users/choose_registration.html')


def pending_approval(request):
    """Show pending approval page for users waiting for admin approval"""
    user = request.user
    role = user.profile.get_role_display() if hasattr(user, 'profile') else 'User'
    
    context = {
        'user': user,
        'role': role,
    }
    
    return render(
        request,
        "users/pending_approval.html",
        context
    )


# ============================================================
# FORGOT PASSWORD FUNCTIONS
# ============================================================

def forgot_password(request):
    """View for users to request password reset"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return redirect('users:forgot_password')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset link
            reset_link = request.build_absolute_uri(
                reverse('users:reset_password', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send reset email
            subject = 'Password Reset - InternHub'
            
            html_message = f'''
            <!DOCTYPE html>
            <html>
            <body>
                <p><strong>Hello {user.username},</strong></p>
                
                <p>You requested a password reset. Click the link below to reset your password:</p>
                
                <p><a href="{reset_link}">{reset_link}</a></p>
                
                <p>This link will expire in 24 hours.</p>
                
                <p>If you didn't request this, please ignore this email.</p>
                
                <p>© InternHub</p>
            </body>
            </html>
            '''
            
            plain_message = f'''
Hello {user.username},

You requested a password reset. Click the link below to reset your password:

{reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

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
            
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('users:login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
            return redirect('users:forgot_password')
    
    return render(request, 'users/forgot_password.html')


def reset_password(request, uidb64, token):
    """View for users to reset their password"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            
            if not password or not password2:
                messages.error(request, 'Both fields are required.')
                return redirect('users:reset_password', uidb64=uidb64, token=token)
            
            if password != password2:
                messages.error(request, 'Passwords do not match.')
                return redirect('users:reset_password', uidb64=uidb64, token=token)
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
                return redirect('users:reset_password', uidb64=uidb64, token=token)
            
            # Set new password
            user.set_password(password)
            user.save()
            
            messages.success(request, 'Password reset successfully! Please login with your new password.')
            return redirect('users:login')
        
        return render(request, 'users/reset_password.html', {'validlink': True})
    else:
        return render(request, 'users/reset_password.html', {'validlink': False})