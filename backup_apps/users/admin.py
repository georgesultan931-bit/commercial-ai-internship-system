from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified')
    list_filter = ('role', 'is_verified')
    search_fields = ('email', 'first_name', 'last_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'organization', 'phone_number', 'profile_picture', 'bio', 'skills', 'is_verified')}),
    )