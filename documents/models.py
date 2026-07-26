from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class DocumentCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='documents/')
    description = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"
    
    def get_file_size(self):
        if self.file:
            return self.file.size
        return 0
    
    def get_file_extension(self):
        if self.file:
            return self.file.name.split('.')[-1].upper()
        return ''