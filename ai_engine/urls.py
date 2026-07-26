from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('insights/', views.AIInsightsView.as_view(), name='insights'),
    path('analyze/', views.AIAnalyzeView.as_view(), name='analyze'),
    path('predictions/', views.AIPredictionsView.as_view(), name='predictions'),
    path('match/', views.ai_match, name='match'),
    path('recommendations/', views.ai_recommendations, name='recommendations'),
    path('upload-resume/', views.upload_resume, name='upload_resume'),
]