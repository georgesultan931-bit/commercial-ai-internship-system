from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class InstitutionProfile(models.Model):

    INSTITUTION_TYPE_CHOICES = (
        ("university", "University"),
        ("college", "College"),
        ("polytechnic", "National Polytechnic"),
        ("tvet", "TVET Institution"),
        ("technical_college", "Technical College"),
        ("other", "Other"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="institution_profile",
    )

    institution_name = models.CharField(
        max_length=255
    )

    institution_type = models.CharField(
        max_length=30,
        choices=INSTITUTION_TYPE_CHOICES,
        default="college",
    )

    registration_number = models.CharField(
        max_length=100,
        blank=True
    )

    official_email = models.EmailField(
        blank=True
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True
    )

    website = models.URLField(
        blank=True
    )

    address = models.CharField(
        max_length=255,
        blank=True
    )

    county = models.CharField(
        max_length=100,
        blank=True
    )

    town = models.CharField(
        max_length=100,
        blank=True
    )

    contact_person_name = models.CharField(
        max_length=150,
        blank=True
    )

    contact_person_position = models.CharField(
        max_length=150,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    logo = models.ImageField(
        upload_to="institution_logos/",
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["institution_name"]

    def __str__(self):
        return self.institution_name


class InstitutionDirectory(models.Model):
    INSTITUTION_TYPE_CHOICES = (
        ("university", "University"),
        ("college", "College"),
        ("polytechnic", "National Polytechnic"),
        ("tvet", "TVET Institution"),
        ("technical_college", "Technical College"),
        ("other", "Other"),
    )

    name = models.CharField(max_length=255, unique=True)
    institution_type = models.CharField(
        max_length=30,
        choices=INSTITUTION_TYPE_CHOICES,
        default="college",
    )
    county = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Institution directory"

    def __str__(self):
        return self.name


class PlacementAssignment(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("assigned", "Assigned"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
        ("suspended", "Suspended"),
        ("cancelled", "Cancelled"),
    )

    institution = models.ForeignKey(
        "institutions.InstitutionProfile",
        on_delete=models.CASCADE,
        related_name="placement_assignments",
    )

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="placement_assignments",
    )

    supervisor = models.ForeignKey(
        "supervisors.SupervisorProfile",
        on_delete=models.SET_NULL,
        related_name="placement_assignments",
        blank=True,
        null=True,
    )

    application = models.OneToOneField(
        "internships.Application",
        on_delete=models.SET_NULL,
        related_name="placement_assignment",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    start_date = models.DateField(
        blank=True,
        null=True
    )

    end_date = models.DateField(
        blank=True,
        null=True
    )

    institution_notes = models.TextField(
        blank=True
    )

    supervisor_notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "institution",
                    "student",
                    "application",
                ],
                name="unique_institution_student_application_assignment",
            )
        ]

    def __str__(self):

        student_name = (
            self.student.full_name
            or self.student.user.username
        )

        return (
            f"{student_name} - "
            f"{self.institution.institution_name}"
        )


class PlacementProgressReport(models.Model):

    STATUS_CHOICES = (
        ("submitted", "Submitted"),
        ("reviewed", "Reviewed"),
        ("revision_required", "Revision Required"),
    )

    assignment = models.ForeignKey(
        PlacementAssignment,
        on_delete=models.CASCADE,
        related_name="progress_reports",
    )

    week_number = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(60),
        ]
    )

    period_start = models.DateField()

    period_end = models.DateField()

    activities = models.TextField(
        help_text="Describe the activities completed during this period."
    )

    skills_gained = models.TextField(
        blank=True
    )

    challenges = models.TextField(
        blank=True
    )

    student_reflection = models.TextField(
        blank=True
    )

    hours_worked = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        validators=[
            MinValueValidator(0)
        ],
    )

    supervisor_comment = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="submitted",
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-week_number",
            "-submitted_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assignment",
                    "week_number",
                ],
                name="unique_assignment_week_report",
            )
        ]

    def __str__(self):
        return (
            f"{self.assignment.student} - "
            f"Week {self.week_number}"
        )


class SupervisorEvaluation(models.Model):

    EVALUATION_TYPE_CHOICES = (
        ("midterm", "Midterm Evaluation"),
        ("final", "Final Evaluation"),
    )

    RECOMMENDATION_CHOICES = (
        ("excellent", "Excellent"),
        ("very_good", "Very Good"),
        ("good", "Good"),
        ("satisfactory", "Satisfactory"),
        ("needs_improvement", "Needs Improvement"),
    )

    assignment = models.ForeignKey(
        PlacementAssignment,
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    supervisor = models.ForeignKey(
        "supervisors.SupervisorProfile",
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    evaluation_type = models.CharField(
        max_length=20,
        choices=EVALUATION_TYPE_CHOICES,
    )

    punctuality_score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    technical_skills_score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    communication_score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    teamwork_score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    initiative_score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    strengths = models.TextField(
        blank=True
    )

    areas_for_improvement = models.TextField(
        blank=True
    )

    general_comments = models.TextField(
        blank=True
    )

    recommendation = models.CharField(
        max_length=30,
        choices=RECOMMENDATION_CHOICES,
        default="satisfactory",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assignment",
                    "evaluation_type",
                ],
                name="unique_assignment_evaluation_type",
            )
        ]

    @property
    def total_score(self):

        return (
            self.punctuality_score
            + self.technical_skills_score
            + self.communication_score
            + self.teamwork_score
            + self.initiative_score
        )

    @property
    def average_score(self):

        return round(
            self.total_score / 5,
            2
        )

    def __str__(self):

        return (
            f"{self.assignment.student} - "
            f"{self.get_evaluation_type_display()}"
        )