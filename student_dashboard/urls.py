from django.urls import path
from . import views

app_name = 'student_dashboard'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('internships/', views.internships, name='internships'),
    path('recommended/', views.recommended, name='recommended'),
    path('applications/', views.applications_view, name='applications'),
    path('saved/', views.saved, name='saved'),
    path('save/<int:internship_id>/', views.save_internship, name='save_internship'),
    path('unsave/<int:internship_id>/', views.unsave_internship, name='unsave_internship'),
]