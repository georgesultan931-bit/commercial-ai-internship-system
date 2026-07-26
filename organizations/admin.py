from django.contrib import admin
from .models import Organization

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'organization_type', 'is_verified', 'created_at')
    list_filter = ('organization_type', 'is_verified')
    search_fields = ('name', 'email', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')