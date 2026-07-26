from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Add your application URLs here
    path('', views.application_list, name='list'),
    path('<int:pk>/', views.application_detail, name='detail'),
    path('apply/<int:internship_id>/', views.apply_to_internship, name='apply'),
    path('status/<int:pk>/update/', views.update_application_status, name='update_status'),
]