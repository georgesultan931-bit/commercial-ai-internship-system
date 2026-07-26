from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('notifications/api/', views.notifications_api, name='notifications_api'),
    path('announcements/', views.announcement_list, name='announcements'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcements/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
    path('announcements/toggle/<int:announcement_id>/', views.toggle_announcement, name='toggle_announcement'),
    path('internships/', views.internship_management, name='internship_management'),
]