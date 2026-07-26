from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('COMPANY_REP', 'Company Representative'),
        ('UNIVERSITY_ADMIN', 'University Admin'),
        ('TVET_ADMIN', 'TVET Admin'),
        ('NGO_ADMIN', 'NGO Admin'),
        ('GOV_AGENCY', 'Government Agency'),
        ('SUPERVISOR', 'Supervisor'),
        ('PLATFORM_ADMIN', 'Platform Admin'),
    )
    
    # Add related_name to avoid clashes with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='custom_user_groups',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_permissions',
        related_query_name='custom_user',
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['organization']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.role})"
    
    @property
    def profile_completion(self):
        required_fields = ['email', 'first_name', 'last_name']
        optional_fields = ['phone_number', 'profile_picture', 'bio', 'skills']
        
        filled = sum(1 for field in required_fields if getattr(self, field))
        filled += sum(1 for field in optional_fields if getattr(self, field) and getattr(self, field) != [])
        
        total = len(required_fields) + len(optional_fields)
        return round((filled / total) * 100)