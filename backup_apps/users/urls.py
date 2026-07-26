from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register-student/', views.RegisterStudentView.as_view(), name='register_student'),
    path('register-employer/', views.RegisterEmployerView.as_view(), name='register_employer'),
    path('register-institution/', views.RegisterInstitutionView.as_view(), name='register_institution'),
    path('choose-registration/', TemplateView.as_view(template_name='users/choose_registration.html'), name='choose_registration'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('verify-email/<str:uidb64>/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('test-email/', views.TestEmailView.as_view(), name='test_email'),      
 
]