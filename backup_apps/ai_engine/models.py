from django.db import models
from django.conf import settings

class AIRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_recommendations')
    internship = models.ForeignKey('internships.Internship', on_delete=models.CASCADE, related_name='ai_recommendations')
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.internship.title} - {self.score}"

class ResumeAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resume_analyses')
    resume_file = models.FileField(upload_to='resumes/')
    analysis_result = models.JSONField(default=dict)
    match_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.match_score}"