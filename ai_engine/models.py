from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AIMatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_matches')
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    match_score = models.IntegerField()  # 0-100
    skills_matched = models.JSONField(default=list)
    skills_missing = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.job_title} ({self.match_score}%)"


class SkillAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_analyses')
    skill_name = models.CharField(max_length=100)
    proficiency = models.IntegerField(default=0)  # 0-100
    demand_level = models.IntegerField(default=0)  # 0-100
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.skill_name}"


class CareerRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='career_recommendations')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=[
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low')
    ], default='Medium')
    action_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"