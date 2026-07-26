from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='documents'),
    path('upload/', views.upload_document, name='upload'),
    path('certificates/', views.certificates, name='certificates'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('<int:doc_id>/', views.document_detail, name='detail'),
    path('<int:doc_id>/delete/', views.delete_document, name='delete'),
    path('<int:doc_id>/verify/', views.verify_document, name='verify'),
]