from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class InstitutionNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('student_registered', 'Student Registered'),
        ('student_approved', 'Student Approved'),
        ('student_placed', 'Student Placed'),
        ('internship_posted', 'Internship Posted'),
        ('organization_verified', 'Organization Verified'),
        ('logbook_submitted', 'Logbook Submitted'),
        ('evaluation_submitted', 'Evaluation Submitted'),
        ('application_received', 'Application Received'),
        ('deadline_reminder', 'Deadline Reminder'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='institution_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='system', link=None):
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )