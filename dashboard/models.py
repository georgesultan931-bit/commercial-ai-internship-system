from django.db import models
from django.conf import settings
from django.utils import timezone

# ============================================
# STUDENT MODELS
# ============================================

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile_dashboard')
    
    # Personal Information
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    GENDER_CHOICES = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('PREFER_NOT_TO_SAY', 'Prefer not to say'),
    )
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    home_address = models.TextField(blank=True)
    postal_address = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    secondary_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Academic Information
    institution_name = models.CharField(max_length=200, blank=True)
    campus = models.CharField(max_length=200, blank=True)
    faculty = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    course = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    admission_number = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    year_of_study = models.IntegerField(null=True, blank=True)
    semester = models.IntegerField(null=True, blank=True)
    expected_graduation_date = models.DateField(null=True, blank=True)
    current_gpa = models.FloatField(null=True, blank=True)
    
    ACADEMIC_LEVEL_CHOICES = (
        ('CERTIFICATE', 'Certificate'),
        ('DIPLOMA', 'Diploma'),
        ('DEGREE', 'Degree'),
        ('MASTERS', 'Masters'),
        ('PHD', 'PhD'),
    )
    academic_level = models.CharField(max_length=20, choices=ACADEMIC_LEVEL_CHOICES, blank=True)
    
    # AI Scores
    resume_score = models.FloatField(default=0.0)
    employability_score = models.FloatField(default=0.0)
    ats_compatibility_score = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"
    
    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def get_profile_completion(self):
        fields = [
            self.profile_photo, self.first_name, self.last_name,
            self.gender, self.date_of_birth, self.national_id,
            self.nationality, self.phone_number, self.email,
            self.institution_name, self.course, self.year_of_study,
            self.current_gpa, self.academic_level
        ]
        filled = sum(1 for f in fields if f)
        total = len(fields)
        return round((filled / total) * 100) if total > 0 else 0


class StudentApplication(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('REVIEWING', 'Under Review'),
        ('INTERVIEW', 'Interview Scheduled'),
        ('OFFERED', 'Offer Extended'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_applications_dashboard')
    internship = models.ForeignKey('internships.Internship', on_delete=models.CASCADE, related_name='student_applications_dashboard')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    cover_letter = models.TextField(blank=True)
    
    ai_match_score = models.FloatField(default=0.0)
    skill_match_percentage = models.FloatField(default=0.0)
    
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'internship']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.internship.title}"


class SavedInternship(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_internships_dashboard')
    internship = models.ForeignKey('internships.Internship', on_delete=models.CASCADE, related_name='saved_by_dashboard')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'internship']
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.student.email} saved {self.internship.title}"


# ============================================
# EMPLOYER MODELS
# ============================================

class CompanyProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_profile_dashboard')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='company_profiles_dashboard')
    
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(blank=True)
    company_size = models.CharField(max_length=50, choices=[
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('500+', '500+ employees'),
    ], blank=True)
    industry = models.CharField(max_length=100, blank=True)
    about = models.TextField(blank=True)
    
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='company_covers/', null=True, blank=True)
    
    is_verified = models.BooleanField(default=False)
    verification_document = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ], default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company_name} - {self.user.email}"


class InterviewSchedule(models.Model):
    application = models.ForeignKey(StudentApplication, on_delete=models.CASCADE, related_name='interviews_dashboard')
    
    interview_date = models.DateTimeField()
    interview_type = models.CharField(max_length=20, choices=[
        ('PHONE', 'Phone Interview'),
        ('VIDEO', 'Video Interview'),
        ('IN_PERSON', 'In-Person Interview'),
        ('TECHNICAL', 'Technical Interview'),
    ], default='VIDEO')
    
    meeting_link = models.URLField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=[
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('RESCHEDULED', 'Rescheduled'),
    ], default='SCHEDULED')
    
    interviewers = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Interview for {self.application.student.email} - {self.interview_date}"


class EmployerMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages_dashboard')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages_dashboard')
    application = models.ForeignKey(StudentApplication, on_delete=models.CASCADE, null=True, blank=True, related_name='messages_dashboard')
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender.email} to {self.recipient.email} - {self.subject}"


class EmployerReport(models.Model):
    REPORT_TYPES = (
        ('APPLICATIONS', 'Applications Report'),
        ('HIRING', 'Hiring Statistics'),
        ('PERFORMANCE', 'Performance Report'),
        ('SKILLS', 'Skills Analysis'),
    )
    
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='reports_dashboard')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    data = models.JSONField(default=dict)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='generated_reports_dashboard')
    
    def __str__(self):
        return f"{self.title} - {self.organization.name}"


# ============================================
# ADDITIONAL EMPLOYER MODELS
# ============================================

class EmployerSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employer_settings_dashboard')
    
    email_notifications = models.BooleanField(default=True)
    application_notifications = models.BooleanField(default=True)
    interview_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    
    ai_matching_enabled = models.BooleanField(default=True)
    ai_resume_analysis = models.BooleanField(default=True)
    ai_candidate_ranking = models.BooleanField(default=True)
    
    two_factor_auth = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Employer Settings"


class SavedCandidate(models.Model):
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_candidates_dashboard')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_by_employers_dashboard')
    application = models.ForeignKey(StudentApplication, on_delete=models.CASCADE, null=True, blank=True, related_name='saved_candidates_dashboard')
    notes = models.TextField(blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['employer', 'student']
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.employer.email} saved {self.student.email}"


class OfferLetter(models.Model):
    application = models.ForeignKey(StudentApplication, on_delete=models.CASCADE, related_name='offer_letters_dashboard')
    content = models.TextField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('EXPIRED', 'Expired'),
    ], default='DRAFT')
    expiry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Offer for {self.application.student.email} - {self.status}"


class InternshipProgress(models.Model):
    internship = models.OneToOneField('internships.Internship', on_delete=models.CASCADE, related_name='progress_dashboard')
    current_interns = models.PositiveIntegerField(default=0)
    total_attendance = models.PositiveIntegerField(default=0)
    weekly_reports_submitted = models.PositiveIntegerField(default=0)
    logbooks_completed = models.PositiveIntegerField(default=0)
    performance_score = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Progress for {self.internship.title}"