from django.urls import path
from django.views.generic import TemplateView

app_name = 'internships'

urlpatterns = [
    path('', TemplateView.as_view(template_name='internships/list.html'), name='list'),
    path('<int:pk>/', TemplateView.as_view(template_name='internships/detail.html'), name='detail'),
]