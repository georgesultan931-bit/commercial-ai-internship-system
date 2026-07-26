from django.contrib import admin
from .models import SupervisorProfile, StudentAssignment


@admin.register(SupervisorProfile)
class SupervisorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'supervisor_id', 'department', 'is_approved', 'is_verified', 'created_at']
    list_filter = ['is_approved', 'is_verified', 'is_active']
    search_fields = ['user__username', 'user__email', 'supervisor_id']


@admin.register(StudentAssignment)
class StudentAssignmentAdmin(admin.ModelAdmin):
    list_display = ['supervisor', 'student', 'status', 'progress_percentage', 'assigned_at']
    list_filter = ['status']
    search_fields = ['supervisor__user__username', 'student__user__username']