from django.urls import path
from . import views

app_name = 'internships'

urlpatterns = [
    path('browse/', views.browse_internships, name='browse'),
    path('recommended/', views.recommended_internships, name='recommended'),
    path('saved/', views.saved_internships, name='saved'),
    path('applications/', views.my_applications, name='applications'),
]