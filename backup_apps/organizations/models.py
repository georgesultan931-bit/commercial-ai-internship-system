from django.db import models
from django.conf import settings

class Organization(models.Model):
    TYPE_CHOICES = (
        ('UNIVERSITY', 'University'),
        ('TVET', 'TVET Institute'),
        ('COMPANY', 'Private Company'),
        ('NGO', 'Non-Governmental Organization'),
        ('GOVERNMENT', 'Government Agency'),
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    organization_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='COMPANY')
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='organization_logos/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name