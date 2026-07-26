from django.db import models
from django.conf import settings

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ], blank=True)
    
    university = models.CharField(max_length=200, blank=True)
    major = models.CharField(max_length=100, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    gpa = models.FloatField(null=True, blank=True)
    
    experience = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    
    ai_embedding = models.JSONField(null=True, blank=True)
    last_ai_update = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Student Profile"
    
    def get_profile_completion(self):
        fields = [
            self.date_of_birth,
            self.university,
            self.major,
            self.graduation_year,
            self.experience,
            self.projects,
            self.user.skills if hasattr(self.user, 'skills') else None
        ]
        filled = sum(1 for f in fields if f)
        total = len(fields)
        return round((filled / total) * 100) if total > 0 else 0


class StudentApplication(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('REVIEWING', 'Under Review'),
        ('INTERVIEW', 'Interview Scheduled'),
        ('OFFERED', 'Offer Extended'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_applications')
    internship = models.ForeignKey('internships.Internship', on_delete=models.CASCADE, related_name='student_applications')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    cover_letter = models.TextField(blank=True)
    
    ai_match_score = models.FloatField(default=0.0)
    skill_match_percentage = models.FloatField(default=0.0)
    
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'internship']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.internship.title}"


class SavedInternship(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_internships')
    internship = models.ForeignKey('internships.Internship', on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'internship']
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.student.email} saved {self.internship.title}"