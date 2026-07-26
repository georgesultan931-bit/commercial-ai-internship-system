from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User
import re

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@example.com'}),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    first_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John'}),
        error_messages={'required': 'First name is required.'}
    )
    last_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doe'}),
        error_messages={'required': 'Last name is required.'}
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        error_messages={'required': 'Password is required.'}
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        error_messages={'required': 'Please confirm your password.'}
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered. Please login or use a different email.')
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password1):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password1):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'[0-9]', password1):
            raise ValidationError('Password must contain at least one number.')
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match. Please try again.')
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.role = 'STUDENT'
        user.is_active = False  # User must verify email first
        if commit:
            user.save()
        return user

class EmployerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'hr@company.com'}),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    company_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
        error_messages={'required': 'Company name is required.'}
    )
    first_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John'}),
        error_messages={'required': 'First name is required.'}
    )
    last_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doe'}),
        error_messages={'required': 'Last name is required.'}
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        error_messages={'required': 'Password is required.'}
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        error_messages={'required': 'Please confirm your password.'}
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered. Please login or use a different email.')
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password1):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password1):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'[0-9]', password1):
            raise ValidationError('Password must contain at least one number.')
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match. Please try again.')
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.role = 'COMPANY_REP'
        user.is_active = False
        if commit:
            user.save()
        return user

class InstitutionRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'admin@university.edu'}),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    institution_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Institution Name'}),
        error_messages={'required': 'Institution name is required.'}
    )
    first_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John'}),
        error_messages={'required': 'First name is required.'}
    )
    last_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doe'}),
        error_messages={'required': 'Last name is required.'}
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        error_messages={'required': 'Password is required.'}
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        error_messages={'required': 'Please confirm your password.'}
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered. Please login or use a different email.')
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password1):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password1):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'[0-9]', password1):
            raise ValidationError('Password must contain at least one number.')
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match. Please try again.')
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.role = 'UNIVERSITY_ADMIN'
        user.is_active = False
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'}),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        error_messages={'required': 'Password is required.'}
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise ValidationError('Invalid email or password. Please try again.')
            if not user.is_active:
                raise ValidationError('Your account is not activated. Please check your email for verification link.')
        return cleaned_data