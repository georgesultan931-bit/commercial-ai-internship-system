from django.contrib import admin
from .models import SupervisorProfile


@admin.register(SupervisorProfile)
class SupervisorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "institution",
        "department",
        "job_title",
        "official_email",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "is_verified",
        "department",
        "institution",
    )

    search_fields = (
        "full_name",
        "staff_number",
        "department",
        "job_title",
        "official_email",
        "phone_number",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "full_name",
    )