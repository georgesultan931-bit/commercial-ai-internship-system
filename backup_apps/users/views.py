from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View, TemplateView
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from .forms import StudentRegistrationForm, EmployerRegistrationForm, InstitutionRegistrationForm, LoginForm
from .models import User


# ============================================
# STUDENT REGISTRATION VIEW
# ============================================
class RegisterStudentView(View):
    template_name = 'users/register_student.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('homepage:dashboard')
        form = StudentRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'STUDENT'
            user.is_active = False
            user.email_verified = False
            user.save()
            
            # Send verification email
            self.send_verification_email(request, user)
            
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('users:login')
        else:
            # Show specific error messages for each field
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
        return render(request, self.template_name, {'form': form})
    
    def send_verification_email(self, request, user):
        current_site = get_current_site(request)
        mail_subject = 'Activate Your InternHub Account'
        message = render_to_string('users/verification_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


# ============================================
# EMPLOYER REGISTRATION VIEW
# ============================================
class RegisterEmployerView(View):
    template_name = 'users/register_employer.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('homepage:dashboard')
        form = EmployerRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = EmployerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'COMPANY_REP'
            user.is_active = False
            user.email_verified = False
            user.save()
            
            # Send verification email
            self.send_verification_email(request, user)
            
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('users:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
        return render(request, self.template_name, {'form': form})
    
    def send_verification_email(self, request, user):
        current_site = get_current_site(request)
        mail_subject = 'Activate Your InternHub Account'
        message = render_to_string('users/verification_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


# ============================================
# INSTITUTION REGISTRATION VIEW
# ============================================
class RegisterInstitutionView(View):
    template_name = 'users/register_institution.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('homepage:dashboard')
        form = InstitutionRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = InstitutionRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'UNIVERSITY_ADMIN'
            user.is_active = False
            user.email_verified = False
            user.save()
            
            # Send verification email
            self.send_verification_email(request, user)
            
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('users:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
        return render(request, self.template_name, {'form': form})
    
    def send_verification_email(self, request, user):
        current_site = get_current_site(request)
        mail_subject = 'Activate Your InternHub Account'
        message = render_to_string('users/verification_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


# ============================================
# LOGIN VIEW
# ============================================
class LoginView(View):
    template_name = 'users/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('homepage:dashboard')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    return redirect('homepage:dashboard')
                else:
                    messages.error(request, 'Your account is not activated. Please check your email for the verification link.')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
        return render(request, self.template_name, {'form': form})


# ============================================
# LOGOUT VIEW
# ============================================
class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('homepage:home')


# ============================================
# REGISTER VIEW (Generic - Choose Registration Type)
# ============================================
class RegisterView(TemplateView):
    template_name = 'users/register.html'


# ============================================
# PROFILE VIEW
# ============================================
@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'users/profile.html'


# ============================================
# EMAIL VERIFICATION VIEW
# ============================================
class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.email_verified = True
            user.save()
            messages.success(request, 'Your email has been verified successfully! You can now login.')
            return redirect('users:login')
        else:
            messages.error(request, 'The verification link is invalid or has expired. Please register again.')
            return redirect('users:register_student')


# ============================================
# TEST EMAIL VIEW
# ============================================
class TestEmailView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login first to test email.')
            return redirect('users:login')
        
        try:
            send_mail(
                'Test Email from InternHub',
                'This is a test email to verify your email configuration is working properly.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],  # Send to the logged-in user's email
                fail_silently=False,
            )
            messages.success(request, f'Test email sent successfully to {request.user.email}! Check your inbox.')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')
        return redirect('homepage:dashboard')