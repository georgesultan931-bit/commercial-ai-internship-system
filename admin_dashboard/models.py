from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    
    # Personal Information
    full_name = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=100, blank=True, default='Administrator')
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Profile Image
    profile_image = models.ImageField(upload_to='admin_profiles/', null=True, blank=True)
    
    # Social Links
    website = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    
    # Settings
    theme_preference = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
    ])
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Admin Profile - {self.user.username}"
    
    def get_full_name(self):
        return self.full_name or self.user.get_full_name() or self.user.username
    
    class Meta:
        verbose_name = "Admin Profile"
        verbose_name_plural = "Admin Profiles"