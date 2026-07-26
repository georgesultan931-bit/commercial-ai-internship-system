from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
# Remove the imports from internships.models for now
# from internships.models import Internship, Organization  # ❌ Remove this

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'dashboard'
        
        # Sample data - will be replaced with real data later
        context['total_internships'] = 12
        context['active_applications'] = 5
        context['messages_count'] = 3
        context['notifications_count'] = 7
        
        return context

# Add other views as needed