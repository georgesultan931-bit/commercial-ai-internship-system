from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Internship(models.Model):
    INTERNSHIP_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('internship', 'Internship'),
        ('volunteer', 'Volunteer'),
    ]
    
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_internships')
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=INTERNSHIP_TYPES, default='internship')
    duration = models.CharField(max_length=100, blank=True, null=True)
    deadline = models.DateField()
    max_applicants = models.IntegerField(default=50)
    company = models.CharField(max_length=200, blank=True, null=True)
    company_image = models.ImageField(upload_to='company_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_application_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_applications_count(self):
        return self.applications.count()
    
    def get_type_display(self):
        return dict(self.INTERNSHIP_TYPES).get(self.type, self.type)


class SavedInternship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_internships')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='saved_by_users')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'internship']
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.internship.title}"