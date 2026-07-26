from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('employer', 'Employer'),
        ('institution', 'Institution'),
        ('supervisor', 'Supervisor'),
        ('coordinator', 'Coordinator'),
        ('government', 'Government'),
        ('ngo', 'NGO'),
        ('admin', 'Admin'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not', 'Prefer not to say'),
    ]

    # Academic Level Choices
    ACADEMIC_LEVEL_CHOICES = [
        ('diploma', 'Diploma'),
        ('degree', 'Degree'),
        ('masters', 'Masters'),
        ('phd', 'PhD'),
        ('certificate', 'Certificate'),
    ]

    # Institution Type Choices
    INSTITUTION_TYPE_CHOICES = [
        ('university', 'University'),
        ('college', 'College'),
        ('tvet', 'TVET'),
        ('institute', 'Institute'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )

    # ============================================================
    # STUDENT FIELDS
    # ============================================================
    admission_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Student registration/admission number"
    )

    institution = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Institution/University name"
    )

    course = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Course or program of study"
    )

    academic_level = models.CharField(
        max_length=20,
        choices=ACADEMIC_LEVEL_CHOICES,
        blank=True,
        null=True,
        help_text="Academic level (Diploma, Degree, Masters, etc.)"
    )

    year_of_study = models.IntegerField(
        default=1,
        help_text="Current year of study"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Phone number"
    )

    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of skills (e.g., Python, Java, Networking)"
    )

    cv = models.FileField(
        upload_to='cvs/',
        blank=True,
        null=True,
        help_text="Upload your CV/Resume"
    )

    # ============================================================
    # EMPLOYER FIELDS
    # ============================================================
    company_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Company name"
    )

    industry = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Industry type (Technology, Healthcare, Finance, etc.)"
    )

    company_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Company email address"
    )

    company_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Company contact phone"
    )

    company_location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Company location"
    )

    company_description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of the company"
    )

    company_logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        help_text="Company logo (optional)"
    )

    website = models.URLField(
        blank=True,
        null=True,
        help_text="Company website (optional)"
    )

    # ============================================================
    # INSTITUTION FIELDS
    # ============================================================
    institution_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Institution name"
    )

    institution_type = models.CharField(
        max_length=20,
        choices=INSTITUTION_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Type of institution"
    )

    institution_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Institution email"
    )

    institution_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Institution phone"
    )

    county = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="County location"
    )

    address = models.TextField(
        blank=True,
        null=True,
        help_text="Physical address (optional)"
    )

    logo = models.ImageField(
        upload_to='institution_logos/',
        blank=True,
        null=True,
        help_text="Institution logo (optional)"
    )

    # ============================================================
    # SUPERVISOR FIELDS
    # ============================================================
    full_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Full name"
    )

    staff_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Staff/Employee ID"
    )

    department = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Department name"
    )

    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Position/Title"
    )

    supervisor_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Phone number"
    )

    supervisor_institution = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Institution name"
    )

    office_location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Office location (optional)"
    )

    supervisor_photo = models.ImageField(
        upload_to='supervisor_photos/',
        blank=True,
        null=True,
        help_text="Profile photo (optional)"
    )

    # ============================================================
    # COMMON FIELDS
    # ============================================================
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    bio = models.TextField(
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    # Documents
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )

    # Verification
    email_verified = models.BooleanField(
        default=False
    )

    verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    # Profile Completion
    is_profile_complete = models.BooleanField(
        default=False
    )

    profile_completion = models.IntegerField(
        default=0
    )

    # Admin Approval
    is_approved = models.BooleanField(
        default=False
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_profiles'
    )

    # AI Fields
    ai_match_score = models.IntegerField(
        default=0
    )

    employability_score = models.IntegerField(
        default=0
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def save(self, *args, **kwargs):
        if self.role == "admin":
            self.is_approved = True
        elif self.role == "student":
            self.is_approved = True
        super().save(*args, **kwargs)

    def get_profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        return f'https://ui-avatars.com/api/?name={self.user.username}&background=4f46e5&color=fff&size=128'

    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    def calculate_completion(self):
        fields = []
        
        if self.role == 'student':
            fields = [
                self.admission_number,
                self.institution,
                self.course,
                self.academic_level,
                self.year_of_study,
                self.phone,
                self.skills,
            ]
        elif self.role == 'employer':
            fields = [
                self.company_name,
                self.industry,
                self.company_email,
                self.company_phone,
                self.company_location,
                self.company_description,
            ]
        elif self.role == 'institution':
            fields = [
                self.institution_name,
                self.institution_type,
                self.institution_email,
                self.institution_phone,
                self.county,
            ]
        elif self.role == 'supervisor':
            fields = [
                self.full_name,
                self.staff_id,
                self.department,
                self.position,
                self.supervisor_phone,
                self.supervisor_institution,
            ]
        else:
            fields = [
                self.phone,
                self.location,
            ]

        completed = len([field for field in fields if field])
        total = len(fields)

        if total > 0:
            self.profile_completion = int((completed / total) * 100)
        else:
            self.profile_completion = 0

        self.is_profile_complete = (self.profile_completion >= 80)

    def requires_approval(self):
        return self.role not in ["student", "admin"]


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()