from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from users.models import UserProfile


class SupervisorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supervisor_profile')
    
    # Basic Info
    supervisor_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    
    # Contact
    phone = models.CharField(max_length=20, blank=True, null=True)
    office_location = models.CharField(max_length=200, blank=True, null=True)
    office_hours = models.CharField(max_length=200, blank=True, null=True)
    
    # Institution Assignment
    institution = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='supervisors',
        limit_choices_to={'role': 'institution'}
    )
    
    # Student Assignments
    assigned_students = models.ManyToManyField(
        UserProfile, 
        blank=True, 
        related_name='assigned_supervisors',
        limit_choices_to={'role': 'student'}
    )
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Supervisor: {self.user.username}"
    
    def get_full_name(self):
        return self.user.get_full_name() or self.user.username


class StudentAssignment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    supervisor = models.ForeignKey(SupervisorProfile, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='supervisor_assignments', limit_choices_to={'role': 'student'})
    
    # Assignment Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    
    # Progress
    progress_percentage = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['supervisor', 'student']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.supervisor.user.username} - {self.student.user.username}"