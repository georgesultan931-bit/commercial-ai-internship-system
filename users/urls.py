from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('choose-registration/', views.choose_registration, name='choose_registration'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    path('upload-profile-image/', views.upload_profile_image, name='upload_profile_image'),
    path('remove-profile-image/', views.remove_profile_image, name='remove_profile_image'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password, name='reset_password'),
]