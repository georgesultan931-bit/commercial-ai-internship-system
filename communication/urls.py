from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('messages/', views.messages_view, name='messages'),
    path('notifications/', views.notifications, name='notifications'),
    path('calendar/', views.calendar, name='calendar'),
    path('inbox/', views.inbox, name='inbox'),
    path('sent/', views.sent_messages, name='sent'),
    path('chat/<int:user_id>/', views.chat, name='chat'),
]