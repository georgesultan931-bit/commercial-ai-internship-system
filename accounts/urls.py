from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('account-start/', views.account_start, name='account_start'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path(
        'admin-profile-image/',
        views.admin_profile_settings,
        name='admin_profile_settings'
    ),

    # Announcements
    path(
        'announcements/',
        views.announcement_center,
        name='announcement_center'
    ),
    path(
        'announcements/feed/',
        views.announcement_feed,
        name='announcement_feed'
    ),
    path(
        'announcements/<int:announcement_id>/read/',
        views.mark_announcement_read,
        name='mark_announcement_read'
    ),
    path(
        'announcements/mark-all-read/',
        views.mark_all_announcements_read,
        name='mark_all_announcements_read'
    ),
    path(
        'announcements/<int:announcement_id>/toggle/',
        views.toggle_announcement_status,
        name='toggle_announcement_status'
    ),
    path(
        'announcements/<int:announcement_id>/delete/',
        views.delete_announcement,
        name='delete_announcement'
    ),

    # Registration
    path('student/register/', views.student_register, name='student_register'),
    path('employer/register/', views.employer_register, name='employer_register'),
    path('register/institution/', views.institution_register, name='institution_register'),
    path('register/supervisor/', views.supervisor_register, name='supervisor_register'),
    path(
        'register/academic-staff/',
        views.academic_staff_register,
        name='academic_staff_register'
    ),

    # Email verification
    path('verify-registration/<token>/', views.verify_registration_email, name='verify_registration_email'),
    path('verify/<token>/', views.verify_registration_email, name='verify_registration_email_legacy'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification_email'),

    # Profile creation
    path('create-student-profile/', views.create_student_profile, name='create_student_profile'),
    path('create-employer-profile/', views.create_employer_profile, name='create_employer_profile'),

    # Admin account actions
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('delete/<int:user_id>/', views.delete_user_account, name='delete_user_account'),
    path('verify-user/<int:user_id>/', views.admin_verify_user, name='admin_verify_user'),
    path('reset-password-admin/<int:user_id>/', views.admin_reset_user_password, name='admin_reset_user_password'),
    path('delete-pending/', views.delete_old_pending_accounts, name='delete_old_pending_accounts'),

    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset-password/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset-password/complete/', views.password_reset_complete, name='password_reset_complete'),
]
