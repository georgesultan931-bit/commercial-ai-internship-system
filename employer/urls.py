from django.urls import path
from . import views

app_name = 'employer'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('post-internship/', views.post_internship, name='post_internship'),
    path('manage-internships/', views.manage_internships, name='manage_internships'),
    path('applications/', views.applications, name='applications'),
    path('company-profile/', views.company_profile, name='company_profile'),
    path('upload-company-logo/', views.upload_company_logo, name='upload_company_logo'),
    path('remove-company-logo/', views.remove_company_logo, name='remove_company_logo'),
]