from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile


# ======================================================
# USER REGISTRATION FORM
# ======================================================

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.core.exceptions import ValidationError

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("❌ This email is already registered. Please use a different email address.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("❌ This username is already taken. Please choose a different username.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


# ======================================================
# BASE PROFILE FORM
# ======================================================

class StyledModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            field.widget.attrs.update({
                "class": "form-control"
            })


# ======================================================
# STUDENT PROFILE
# ======================================================

class StudentProfileForm(StyledModelForm):

    class Meta:

        model = UserProfile

        fields = [

            "phone",
            "location",
            "gender",
            "date_of_birth",

            "institution",
            "faculty",
            "course",
            "admission_number",
            "year_of_study",

            "skills",

            "profile_image",
            "resume",

            "bio",

        ]


# ======================================================
# EMPLOYER PROFILE
# ======================================================

class EmployerProfileForm(StyledModelForm):

    class Meta:

        model = UserProfile

        fields = [

            "phone",
            "location",

            "company_name",
            "company_registration",
            "industry",

            "profile_image",

            "bio",

        ]


# ======================================================
# SUPERVISOR PROFILE
# ======================================================

class SupervisorProfileForm(StyledModelForm):

    class Meta:

        model = UserProfile

        fields = [

            "phone",
            "location",

            "specialization",

            "profile_image",

            "bio",

        ]


# ======================================================
# INSTITUTION PROFILE
# ======================================================

class InstitutionProfileForm(StyledModelForm):

    class Meta:

        model = UserProfile

        fields = [

            "phone",
            "location",

            "profile_image",

            "bio",

        ]


# ======================================================
# COORDINATOR PROFILE
# ======================================================

class CoordinatorProfileForm(StyledModelForm):

    class Meta:

        model = UserProfile

        fields = [

            "phone",
            "location",

            "profile_image",

            "bio",

        ]