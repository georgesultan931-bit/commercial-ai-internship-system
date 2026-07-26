from django.contrib import admin
from .models import ChatRoom, Message, Notification


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'room_type', 'name', 'created_by', 'is_active', 'created_at']
    list_filter = ['room_type', 'is_active']
    filter_horizontal = ['participants']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'sender', 'content', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read']
    search_fields = ['content']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipient', 'sender', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['title', 'message']