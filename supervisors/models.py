from django.conf import settings
from django.db import models


class SupervisorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="supervisor_profile",
    )

    institution = models.ForeignKey(
        "institutions.InstitutionProfile",
        on_delete=models.SET_NULL,
        related_name="supervisors",
        blank=True,
        null=True,
    )

    full_name = models.CharField(
        max_length=200
    )

    staff_number = models.CharField(
        max_length=100,
        blank=True,
    )

    department = models.CharField(
        max_length=150,
        blank=True,
    )

    job_title = models.CharField(
        max_length=150,
        blank=True,
    )

    specialization = models.CharField(
        max_length=200,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    official_email = models.EmailField(
        blank=True,
    )

    bio = models.TextField(
        blank=True,
    )

    profile_picture = models.ImageField(
        upload_to="supervisor_profiles/",
        blank=True,
        null=True,
    )

    is_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name