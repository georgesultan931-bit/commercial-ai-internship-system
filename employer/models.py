from django.db import models
from django.contrib.auth.models import User
from users.models import UserProfile


class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    
    # Company Images
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    company_cover_image = models.ImageField(upload_to='company_covers/', blank=True, null=True)
    company_images = models.JSONField(default=list, blank=True)  # Multiple images
    
    # Company Details
    company_name = models.CharField(max_length=200, blank=True)
    company_registration = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    website = models.URLField(blank=True)
    
    # Social Links
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    
    # Status
    is_approved = models.BooleanField(default=False)
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.company_name or self.user.username