from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from internships.models import Internship, Application
from .services import AIService
from .models import ResumeAnalysis, AIRecommendation, CandidateRanking

# Initialize AI Service
ai_service = AIService()


@login_required(login_url='/users/login/')
def upload_resume(request):
    """Upload and analyze resume"""
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        
        if not resume_file:
            messages.error(request, 'Please select a resume file.')
            return redirect('ai_engine:ai_matching')
        
        # Check file type
        file_ext = resume_file.name.split('.')[-1].lower()
        if file_ext not in ['pdf', 'docx']:
            messages.error(request, 'Please upload a PDF or DOCX file.')
            return redirect('ai_engine:ai_matching')
        
        # Analyze resume
        result = ai_service.analyze_resume(request.user, resume_file)
        
        if result.get('error'):
            messages.error(request, result['error'])
            return redirect('ai_engine:ai_matching')
        
        messages.success(request, f'Resume analyzed successfully! Found {result.get("skill_count", 0)} skills.')
        return redirect('ai_engine:ai_matching')
    
    return redirect('ai_engine:ai_matching')


@login_required(login_url='/users/login/')
def ai_matching(request):
    """AI Matching page"""
    user = request.user
    
    # Check if user has resume analysis
    try:
        analysis = ResumeAnalysis.objects.get(user=user)
        has_resume = True
    except ResumeAnalysis.DoesNotExist:
        analysis = None
        has_resume = False
    
    # Get AI recommendations for student
    recommendations = []
    if user.profile.role == 'STUDENT' and has_resume:
        result = ai_service.get_recommendations_for_student(user, limit=5)
        recommendations = result.get('recommendations', [])
    
    # Get recent matches
    recent_matches = []
    if has_resume:
        # Get internships the student has applied to with match scores
        applications = Application.objects.filter(
            applicant=user
        ).select_related('internship')
        
        for app in applications:
            recent_matches.append({
                'internship': app.internship,
                'status': app.status,
                'applied_at': app.applied_at,
            })
    
    context = {
        'has_resume': has_resume,
        'analysis': analysis,
        'recommendations': recommendations,
        'recent_matches': recent_matches,
        'skills': analysis.skills if analysis else [],
    }
    
    return render(request, 'ai_engine/ai_matching.html', context)


@login_required(login_url='/users/login/')
def get_recommendations_api(request):
    """API endpoint for AI recommendations"""
    if request.user.profile.role != 'STUDENT':
        return JsonResponse({'error': 'Only students can access this feature.'}, status=403)
    
    result = ai_service.get_recommendations_for_student(request.user, limit=10)
    
    if result.get('error'):
        return JsonResponse({'error': result['error']}, status=400)
    
    return JsonResponse(result)


@login_required(login_url='/users/login/')
def rank_candidates_api(request, internship_id):
    """API endpoint for candidate ranking (Employers only)"""
    internship = get_object_or_404(Internship, id=internship_id)
    
    # Check permission
    try:
        if internship.organization != request.user.profile.organization:
            return JsonResponse({'error': 'Permission denied.'}, status=403)
    except:
        return JsonResponse({'error': 'Please complete your profile first.'}, status=400)
    
    result = ai_service.rank_candidates(internship)
    
    if result.get('error'):
        return JsonResponse({'error': result['error']}, status=400)
    
    return JsonResponse(result)


@login_required(login_url='/users/login/')
def view_analysis(request):
    """View resume analysis results"""
    try:
        analysis = ResumeAnalysis.objects.get(user=request.user)
    except ResumeAnalysis.DoesNotExist:
        messages.info(request, 'Please upload and analyze your resume first.')
        return redirect('ai_engine:ai_matching')
    
    context = {
        'analysis': analysis,
        'skills': analysis.skills,
        'experience': analysis.experience,
        'education': analysis.education,
    }
    return render(request, 'ai_engine/resume_analysis.html', context)