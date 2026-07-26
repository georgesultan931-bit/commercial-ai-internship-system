from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboards
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('employer/', views.employer_dashboard, name='employer_dashboard'),
    path('institution/', views.institution_dashboard, name='institution_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Admin Approval
    path('admin/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('admin/reject/<int:user_id>/', views.reject_user, name='reject_user'),
    
    # Admin Management
    path('admin/organizations/', views.manage_organizations, name='manage_organizations'),
    path('admin/users/', views.manage_users, name='manage_users'),
    path('admin/analytics/', views.platform_analytics, name='platform_analytics'),
    path('admin/settings/', views.system_settings, name='system_settings'),
    path('admin/audit/', views.audit_logs, name='audit_logs'),
]