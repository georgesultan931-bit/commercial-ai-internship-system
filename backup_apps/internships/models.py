from django.db import models
from django.conf import settings
from django.utils import timezone

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


class Internship(models.Model):
    CATEGORY_CHOICES = (
        ('DEVELOPMENT', 'Development'),
        ('DESIGN', 'Design'),
        ('MARKETING', 'Marketing'),
        ('BUSINESS', 'Business'),
        ('DATA_SCIENCE', 'Data Science'),
        ('OTHER', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CLOSED', 'Closed'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='posted_internships')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_internships')
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='internships')
    
    location = models.CharField(max_length=200, default='Remote')
    is_remote = models.BooleanField(default=False)
    
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateTimeField(null=True, blank=True)
    
    max_applicants = models.PositiveIntegerField(default=10)
    current_applicants = models.PositiveIntegerField(default=0)
    
    required_skills = models.JSONField(default=list, blank=True)
    preferred_skills = models.JSONField(default=list, blank=True)
    requirements = models.TextField(blank=True)
    
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_internships')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    ai_recommendation_score = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.organization.name})"
    
    @property
    def is_application_open(self):
        return (self.status == 'APPROVED' and 
                self.current_applicants < self.max_applicants and
                self.is_active and
                (self.application_deadline is None or timezone.now() < self.application_deadline))