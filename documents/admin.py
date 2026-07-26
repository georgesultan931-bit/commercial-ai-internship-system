from django.contrib import admin
from .models import Document, DocumentCategory


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'is_verified', 'uploaded_at']
    list_filter = ['is_verified', 'category']
    search_fields = ['title', 'user__username']
    readonly_fields = ['uploaded_at', 'updated_at']