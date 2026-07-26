from django.db import models
from django.contrib.auth.models import User
from internships.models import Internship


class Application(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWING', 'Reviewing'),
        ('SHORTLISTED', 'Shortlisted'),
        ('INTERVIEW', 'Interview'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    cover_letter = models.TextField(blank=True, null=True)
    applied_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-applied_date']
        unique_together = ['internship', 'applicant']
    
    def __str__(self):
        return f"{self.applicant.username} - {self.internship.title}"
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)