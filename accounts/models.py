from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

import random


class User(AbstractUser):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("employer", "Employer"),
        ("institution", "Institution"),
        ("supervisor", "Supervisor"),
        ("lecturer", "Lecturer"),
        ("hod", "Head of Department"),
        ("dean", "Dean"),
        ("admin", "Admin"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )
    is_email_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp_code

    def __str__(self):
        return self.username


class Announcement(models.Model):
    AUDIENCE_CHOICES = (
        ("all", "Everyone"),
        ("student", "Students"),
        ("employer", "Employers"),
        ("institution", "Institutions"),
        ("supervisor", "Supervisors"),
        ("lecturer", "Lecturers"),
        ("hod", "Heads of Department"),
        ("dean", "Deans"),
    )

    PRIORITY_CHOICES = (
        ("normal", "Normal"),
        ("important", "Important"),
        ("urgent", "Urgent"),
    )

    title = models.CharField(max_length=180)
    message = models.TextField()
    audience = models.CharField(
        max_length=20,
        choices=AUDIENCE_CHOICES,
        default="all",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="normal",
    )
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_announcements",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())


class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="read_records",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="announcement_reads",
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["announcement", "user"],
                name="unique_announcement_read_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.announcement}"
