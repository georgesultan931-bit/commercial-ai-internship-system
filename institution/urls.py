from django.urls import path
from . import views

app_name = 'institution'

urlpatterns = [
    path('', views.InstitutionDashboardView.as_view(), name='dashboard'),
    path('profile/', views.InstitutionProfileView.as_view(), name='profile'),
    path('students/', views.StudentManagementView.as_view(), name='students'),
    path('students/register/', views.RegisterStudentView.as_view(), name='register_student'),
    path('students/approve/<int:pk>/', views.ApproveStudentView.as_view(), name='approve_student'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('placements/', views.PlacementManagementView.as_view(), name='placements'),
    path('internships/', views.InternshipOpportunitiesView.as_view(), name='internships'),
    path('organizations/', views.OrganizationManagementView.as_view(), name='organizations'),
    path('supervisors/', views.SupervisorManagementView.as_view(), name='supervisors'),
    path('logbooks/', views.LogbookManagementView.as_view(), name='logbooks'),
    path('evaluations/', views.EvaluationManagementView.as_view(), name='evaluations'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('messages/', views.MessagesView.as_view(), name='messages'),
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('notifications/mark/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/delete/<int:pk>/', views.delete_notification, name='delete_notification'),
    path('notifications/api/', views.get_notifications_api, name='notifications_api'),
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('documents/', views.DocumentsView.as_view(), name='documents'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]