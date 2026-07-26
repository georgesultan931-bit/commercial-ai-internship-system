from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'applicant', 'internship', 'status', 'applied_date']
    list_filter = ['status', 'applied_date']
    search_fields = ['applicant__username', 'internship__title']
    readonly_fields = ['applied_date', 'updated_at']