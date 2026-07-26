from django.urls import path
from . import views

app_name = 'homepage'

urlpatterns = [
    # Main pages
    path('', views.HomePageView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('browse-internships/', views.BrowseInternshipsView.as_view(), name='browse_internships'),
    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('saved/', views.SavedView.as_view(), name='saved'),
    
    # AI Tools
    path('ai-match/', views.AIMatchView.as_view(), name='ai_match'),
    path('resume-builder/', views.ResumeBuilderView.as_view(), name='resume_builder'),
    path('cover-letter/', views.CoverLetterView.as_view(), name='cover_letter'),
    
    # Account
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    
    # Public pages
    path('about/', views.AboutPageView.as_view(), name='about'),
    path('features/', views.FeaturesPageView.as_view(), name='features'),
    path('pricing/', views.PricingPageView.as_view(), name='pricing'),
    path('contact/', views.ContactPageView.as_view(), name='contact'),
]