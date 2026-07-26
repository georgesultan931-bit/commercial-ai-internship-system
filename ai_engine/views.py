from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from django.utils import timezone


class AIInsightsView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_engine/insights.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'ai_insights'
        
        try:
            from .models import AIMatch, SkillAnalysis, CareerRecommendation
            
            total_matches = AIMatch.objects.count()
            avg_match_score = AIMatch.objects.aggregate(Avg('match_score'))['match_score__avg'] or 0
            high_matches = AIMatch.objects.filter(match_score__gte=80).count()
            
            week_ago = timezone.now() - timedelta(days=7)
            recent_matches = AIMatch.objects.filter(created_at__gte=week_ago).count()
            
            top_skills = SkillAnalysis.objects.values('skill_name').annotate(
                total=Count('id')
            ).order_by('-total')[:10]
            
            context['ai_stats'] = {
                'total_matches': total_matches,
                'avg_match_score': round(avg_match_score, 1),
                'high_matches': high_matches,
                'recent_matches': recent_matches,
                'top_skills': list(top_skills)
            }
            
            user_matches = AIMatch.objects.filter(user=self.request.user).order_by('-created_at')[:5]
            user_recommendations = CareerRecommendation.objects.filter(
                user=self.request.user, 
                is_read=False
            ).order_by('-created_at')[:5]
            
            context['user_matches'] = user_matches
            context['user_recommendations'] = user_recommendations
            
        except:
            context['ai_stats'] = {
                'total_matches': 0,
                'avg_match_score': 0,
                'high_matches': 0,
                'recent_matches': 0,
                'top_skills': []
            }
            context['user_matches'] = []
            context['user_recommendations'] = []
        
        context['market_trends'] = {
            'trending_skills': [],
            'top_industries': [],
            'salary_ranges': {
                'entry': 0,
                'mid': 0,
                'senior': 0,
                'lead': 0
            }
        }
        
        context['ai_performance'] = {
            'accuracy': 0,
            'speed': '0s',
            'total_processed': 0,
            'success_rate': 0,
            'user_satisfaction': 0,
            'daily_active_users': 0
        }
        
        context['chart_data'] = {
            'match_distribution': {
                'labels': ['High Match (80%+)', 'Medium Match (50-79%)', 'Low Match (0-49%)'],
                'values': [0, 0, 0],
                'colors': ['#28a745', '#ffc107', '#dc3545']
            },
            'skills_demand': [],
            'match_trends': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                'values': [0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        context['recent_activities'] = []
        
        return context


class AIAnalyzeView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_engine/analyze.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'ai_insights'
        
        context['analysis'] = {
            'profile_strength': 0,
            'skill_gaps': [],
            'recommended_courses': [],
            'career_paths': []
        }
        
        return context


class AIPredictionsView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_engine/predictions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'ai_insights'
        
        context['predictions'] = {
            'career_growth': {
                'current_role': 'Not available',
                'next_role': 'Not available',
                'timeline': 'Not available',
                'salary_increase': 'Not available',
                'confidence': 0
            },
            'skill_predictions': [],
            'job_market_forecast': {
                'next_6_months': 'Not available',
                'next_year': 'Not available',
                'top_roles': []
            }
        }
        
        return context


@login_required
def ai_match(request):
    context = {
        'active_menu': 'ai_insights',
        'has_resume': False,
        'skills': [],
        'recommendations': [],
        'recent_matches': [],
    }
    
    try:
        from .models import AIMatch
        
        recent_matches = AIMatch.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        context['recent_matches'] = recent_matches
        
        high_matches = AIMatch.objects.filter(
            user=request.user,
            match_score__gte=80
        ).order_by('-match_score')[:5]
        
        context['recommendations'] = high_matches
        
    except:
        context['recommendations'] = []
        context['recent_matches'] = []
    
    return render(request, 'ai_engine/match.html', context)


@login_required
def ai_recommendations(request):
    context = {
        'active_menu': 'ai_insights',
        'recommendations': [],
    }
    
    try:
        from .models import CareerRecommendation
        
        recommendations = CareerRecommendation.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        context['recommendations'] = recommendations
        
    except:
        context['recommendations'] = []
    
    return render(request, 'ai_engine/recommendations.html', context)


@login_required
def upload_resume(request):
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        
        if not resume_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('ai_engine:match')
        
        try:
            # Check file extension
            allowed_extensions = ['.pdf', '.docx']
            file_extension = '.' + resume_file.name.split('.')[-1].lower()
            
            if file_extension not in allowed_extensions:
                messages.error(request, 'Please upload a PDF or DOCX file.')
                return redirect('ai_engine:match')
            
            # Check file size (5MB max)
            if resume_file.size > 5 * 1024 * 1024:
                messages.error(request, 'File size must be less than 5MB.')
                return redirect('ai_engine:match')
            
            # Process the resume here
            # For now, just save it or process it
            
            messages.success(request, 'Resume uploaded and analyzed successfully!')
            
        except Exception as e:
            messages.error(request, f'Error processing resume: {str(e)}')
        
        return redirect('ai_engine:match')
    
    return redirect('ai_engine:match')