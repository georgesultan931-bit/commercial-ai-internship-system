from django.contrib import admin
from .models import Organization

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'organization_type', 'is_verified')
    list_filter = ('organization_type', 'is_verified')
    search_fields = ('name', 'email')
    prepopulated_fields = {'slug': ('name',)}