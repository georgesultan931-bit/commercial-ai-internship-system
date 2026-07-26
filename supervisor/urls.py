from django.urls import path
from . import views

app_name = 'supervisor'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('assigned-students/', views.assigned_students, name='assigned_students'),
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('internship-monitoring/', views.internship_monitoring, name='internship_monitoring'),
    path('logbooks/', views.logbooks, name='logbooks'),
    path('evaluations/', views.evaluations, name='evaluations'),
    path('reports/', views.reports, name='reports'),
    path('messages/', views.messages_view, name='messages'),
    path('settings/', views.settings, name='settings'),
]