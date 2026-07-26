from django.db import models
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    TYPE_CHOICES = (
        ('UNIVERSITY', 'University'),
        ('TVET', 'TVET Institute'),
        ('COMPANY', 'Private Company'),
        ('NGO', 'Non-Governmental Organization'),
        ('GOVERNMENT', 'Government Agency'),
        ('OTHER', 'Other'),
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    organization_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='COMPANY'
    )
    
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='organization_logos/', null=True, blank=True)
    
    is_verified = models.BooleanField(default=False)
    verification_document = models.FileField(
        upload_to='verification_docs/',
        null=True,
        blank=True
    )
    
    subscription_plan = models.CharField(max_length=50, default='free')
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    
    settings = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['organization_type']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return self.name