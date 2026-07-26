from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from users.models import UserProfile
from internships.models import Internship
from applications.models import Application
from .models import InstitutionNotification


class InstitutionDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/dashboard.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_dashboard'
        
        total_students = User.objects.filter(profile__role='student').count()
        students_on_attachment = Application.objects.filter(status='ACCEPTED').count()
        students_not_placed = total_students - students_on_attachment
        active_employers = User.objects.filter(profile__role='employer', is_active=True).count()
        available_internships = Internship.objects.filter(is_active=True).count()
        
        placement_rate = int((students_on_attachment / total_students) * 100) if total_students > 0 else 0
        
        recent_activities = Application.objects.order_by('-applied_date')[:5]
        
        context['total_students'] = total_students
        context['students_on_attachment'] = students_on_attachment
        context['students_not_placed'] = students_not_placed
        context['active_employers'] = active_employers
        context['available_internships'] = available_internships
        context['placement_rate'] = placement_rate
        context['recent_activities'] = recent_activities
        
        return context


class InstitutionProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/profile.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        if 'upload_image' in request.POST:
            if request.FILES.get('profile_image'):
                try:
                    user.profile.profile_image = request.FILES['profile_image']
                    user.profile.save()
                    messages.success(request, 'Profile image uploaded successfully!')
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')
            else:
                messages.error(request, 'Please select an image to upload.')
            return redirect('institution:profile')
        
        if 'update_profile' in request.POST:
            institution_name = request.POST.get('institution_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            bio = request.POST.get('bio')
            
            if institution_name:
                name_parts = institution_name.split(' ', 1)
                user.first_name = name_parts[0]
                user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            if email:
                user.email = email
            
            user.save()
            
            if phone is not None:
                user.profile.phone = phone
            if location is not None:
                user.profile.location = location
            if bio is not None:
                user.profile.bio = bio
            
            user.profile.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('institution:profile')
        
        return redirect('institution:profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_profile'
        return context


class StudentManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/students.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_students'
        context['students'] = User.objects.filter(profile__role='student').order_by('-date_joined')
        return context


class RegisterStudentView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/register_student.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_students'
        return context


class ApproveStudentView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/approve_student.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_students'
        student = get_object_or_404(User, pk=kwargs.get('pk'))
        context['student'] = student
        return context


class StudentDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/student_detail.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_students'
        student = get_object_or_404(User, pk=kwargs.get('pk'))
        context['student'] = student
        return context


class PlacementManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/placements.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_placements'
        context['placed_students'] = Application.objects.filter(status='ACCEPTED')
        context['pending_students'] = User.objects.filter(profile__role='student').exclude(
            applications__status='ACCEPTED'
        )
        return context


class InternshipOpportunitiesView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/internships.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_internships'
        context['internships'] = Internship.objects.filter(is_active=True).order_by('-created_at')
        return context


class OrganizationManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/organizations.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_organizations'
        context['organizations'] = User.objects.filter(profile__role='employer')
        return context


class SupervisorManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/supervisors.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_supervisors'
        context['supervisors'] = User.objects.filter(profile__role='supervisor')
        return context


class LogbookManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/logbooks.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_logbooks'
        return context


class EvaluationManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/evaluations.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_evaluations'
        return context


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/reports.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_reports'
        return context


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/analytics.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_analytics'
        return context


class MessagesView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/messages.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_messages'
        return context


class NotificationsView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/notifications.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_notifications'
        
        notifications = InstitutionNotification.objects.filter(user=self.request.user)
        notifications.filter(is_read=False).update(is_read=True)
        
        context['notifications'] = notifications
        
        return context


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/calendar.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_calendar'
        return context


class DocumentsView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/documents.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_documents'
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'institution/settings.html'
    login_url = 'account_login'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            if request.user.profile.role != 'institution':
                return redirect('homepage:home')
        except UserProfile.DoesNotExist:
            return redirect('homepage:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'institution_settings'
        return context


@csrf_exempt
@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(InstitutionNotification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, 'Notification marked as read.')
    return redirect('institution:notifications')


@csrf_exempt
@login_required
def mark_all_notifications_read(request):
    InstitutionNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('institution:notifications')


@csrf_exempt
@login_required
def delete_notification(request, pk):
    notification = get_object_or_404(InstitutionNotification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, 'Notification deleted.')
    return redirect('institution:notifications')


@csrf_exempt
@login_required
def get_notifications_api(request):
    notifications = InstitutionNotification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:10]
    
    data = {
        'count': notifications.count(),
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
                'link': n.link,
            } for n in notifications
        ]
    }
    return JsonResponse(data)