from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    path('create/', views.create_chat, name='create_chat'),
    path('send/<int:room_id>/', views.send_message, name='send_message'),
    path('messages/<int:room_id>/', views.get_messages, name='get_messages'),
    path('mark-read/<int:room_id>/', views.mark_read, name='mark_read'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/api/', views.notifications_api, name='notifications_api'),
    path('unread-count/', views.unread_count_api, name='unread_count_api'),
]