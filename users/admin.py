from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'email_verified',
        'is_profile_complete',
        'is_approved',
        'created_at',
    )

    list_filter = (
        'role',
        'email_verified',
        'is_approved',
    )

    search_fields = (
        'user__username',
        'user__email',
    )