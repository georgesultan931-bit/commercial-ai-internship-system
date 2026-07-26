from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    # Main AI Matching Page
    path('matching/', views.ai_matching, name='ai_matching'),
    
    # Resume Upload
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    
    # API Endpoints
    path('api/recommendations/', views.get_recommendations_api, name='get_recommendations_api'),
    path('api/rank/<int:internship_id>/', views.rank_candidates_api, name='rank_candidates_api'),
    
    # View Analysis
    path('analysis/', views.view_analysis, name='view_analysis'),
]