from django.shortcuts import render
from django.views.generic import TemplateView

# ============================================
# MAIN PAGES
# ============================================
class HomePageView(TemplateView):
    template_name = 'homepage/home.html'

class DashboardView(TemplateView):
    template_name = 'homepage/dashboard.html'

class BrowseInternshipsView(TemplateView):
    template_name = 'homepage/browse_internships.html'

class MyApplicationsView(TemplateView):
    template_name = 'homepage/my_applications.html'

class SavedView(TemplateView):
    template_name = 'homepage/saved.html'

# ============================================
# AI TOOLS
# ============================================
class AIMatchView(TemplateView):
    template_name = 'homepage/ai_match.html'

class ResumeBuilderView(TemplateView):
    template_name = 'homepage/resume_builder.html'

class CoverLetterView(TemplateView):
    template_name = 'homepage/cover_letter.html'

# ============================================
# ACCOUNT
# ============================================
class ProfileView(TemplateView):
    template_name = 'homepage/profile.html'

class SettingsView(TemplateView):
    template_name = 'homepage/settings.html'

class NotificationsView(TemplateView):
    template_name = 'homepage/notifications.html'

# ============================================
# PUBLIC PAGES
# ============================================
class AboutPageView(TemplateView):
    template_name = 'homepage/about.html'

class FeaturesPageView(TemplateView):
    template_name = 'homepage/features.html'

class PricingPageView(TemplateView):
    template_name = 'homepage/pricing.html'

class ContactPageView(TemplateView):
    template_name = 'homepage/contact.html'