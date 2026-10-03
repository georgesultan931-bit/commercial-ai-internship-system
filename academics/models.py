from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SchoolFaculty(models.Model):
    institution = models.ForeignKey(
        "institutions.InstitutionProfile",
        on_delete=models.CASCADE,
        related_name="schools_faculties",
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["institution__institution_name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_school_name_per_institution",
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.institution.institution_name}"


class Department(models.Model):
    school = models.ForeignKey(
        SchoolFaculty,
        on_delete=models.CASCADE,
        related_name="departments",
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["school__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_department_name_per_school",
            )
        ]

    @property
    def institution(self):
        return self.school.institution

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Programme(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="programmes",
    )
    name = models.CharField(max_length=220)
    code = models.CharField(max_length=40, blank=True, default="")
    qualification_level = models.CharField(max_length=100, blank=True, default="")
    duration_years = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["department__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="unique_programme_name_per_department",
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.department.name}"


class AcademicStaffProfile(models.Model):
    ROLE_CHOICES = (
        ("lecturer", "Lecturer"),
        ("hod", "Head of Department"),
        ("dean", "Dean"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academic_staff_profile",
    )
    institution = models.ForeignKey(
        "institutions.InstitutionProfile",
        on_delete=models.CASCADE,
        related_name="academic_staff",
    )
    school = models.ForeignKey(
        SchoolFaculty,
        on_delete=models.CASCADE,
        related_name="academic_staff",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="academic_staff",
        blank=True,
        null=True,
    )
    academic_role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
    )
    staff_number = models.CharField(max_length=80, blank=True, default="")
    job_title = models.CharField(max_length=150, blank=True, default="")
    phone_number = models.CharField(max_length=30, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "institution__institution_name",
            "school__name",
            "academic_role",
            "user__username",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["school"],
                condition=models.Q(academic_role="dean", is_active=True),
                name="one_active_dean_per_school",
            ),
            models.UniqueConstraint(
                fields=["department"],
                condition=models.Q(academic_role="hod", is_active=True),
                name="one_active_hod_per_department",
            ),
        ]

    def clean(self):
        errors = {}

        if self.user_id and self.user.role not in {"lecturer", "hod", "dean"}:
            errors["user"] = (
                "Academic staff accounts must have the Lecturer, HOD or Dean role."
            )

        if self.school_id and self.institution_id:
            if self.school.institution_id != self.institution_id:
                errors["school"] = "The school/faculty must belong to the selected institution."

        if self.department_id and self.school_id:
            if self.department.school_id != self.school_id:
                errors["department"] = "The department must belong to the selected school/faculty."

        if self.academic_role in {"lecturer", "hod"} and not self.department_id:
            errors["department"] = (
                "A Lecturer or Head of Department must be assigned to a department."
            )

        if self.academic_role == "dean" and self.department_id:
            errors["department"] = "A Dean is assigned at school/faculty level, not to one department."

        if self.user_id and self.academic_role and self.user.role != self.academic_role:
            errors["academic_role"] = "The profile role must match the user's account role."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.get_academic_role_display()}"


class AcademicYear(models.Model):
    institution = models.ForeignKey(
        "institutions.InstitutionProfile",
        on_delete=models.CASCADE,
        related_name="academic_years",
    )
    name = models.CharField(max_length=40)
    starts_on = models.DateField()
    ends_on = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-starts_on"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_academic_year_per_institution",
            )
        ]

    def clean(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValidationError({"ends_on": "Academic year end date cannot be before its start date."})

    def __str__(self):
        return f"{self.name} - {self.institution.institution_name}"


class Semester(models.Model):
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="semesters",
    )
    name = models.CharField(max_length=60)
    number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    starts_on = models.DateField()
    ends_on = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["academic_year", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "number"],
                name="unique_semester_number_per_year",
            )
        ]

    def clean(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValidationError({"ends_on": "Semester end date cannot be before its start date."})

    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"


class Unit(models.Model):
    programme = models.ForeignKey(
        Programme,
        on_delete=models.CASCADE,
        related_name="units",
    )
    code = models.CharField(max_length=40)
    title = models.CharField(max_length=220)
    year_of_study = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    semester_number = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
    )
    credit_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = [
            "programme__name",
            "year_of_study",
            "semester_number",
            "code",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["programme", "code"],
                name="unique_unit_code_per_programme",
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"


class LecturerUnitAssignment(models.Model):
    lecturer = models.ForeignKey(
        AcademicStaffProfile,
        on_delete=models.CASCADE,
        related_name="unit_assignments",
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="lecturer_assignments",
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        related_name="lecturer_unit_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="lecturer_unit_assignments_created",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "-semester__academic_year__starts_on",
            "unit__code",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "semester"],
                name="unique_lecturer_unit_per_semester",
            )
        ]

    def clean(self):
        errors = {}

        if self.lecturer_id:
            if self.lecturer.academic_role != "lecturer":
                errors["lecturer"] = "Only an active Lecturer profile can teach a unit."
            elif not self.lecturer.is_active:
                errors["lecturer"] = "The selected Lecturer profile is inactive."

        if self.lecturer_id and self.unit_id:
            if self.lecturer.department_id != self.unit.programme.department_id:
                errors["unit"] = "The unit must belong to the Lecturer's department."

        if self.lecturer_id and self.semester_id:
            if (
                self.lecturer.institution_id
                != self.semester.academic_year.institution_id
            ):
                errors["semester"] = (
                    "The semester must belong to the Lecturer's institution."
                )

        if self.unit_id and self.semester_id:
            if self.unit.semester_number != self.semester.number:
                errors["semester"] = (
                    "The semester number must match the unit configuration."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.lecturer.user.username} - "
            f"{self.unit.code} - {self.semester}"
        )


class StudentAcademicAssignment(models.Model):
    student = models.OneToOneField(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="academic_assignment",
    )

    institution = models.ForeignKey(
        "institutions.InstitutionProfile",
        on_delete=models.CASCADE,
        related_name="student_academic_assignments",
    )

    school = models.ForeignKey(
        SchoolFaculty,
        on_delete=models.CASCADE,
        related_name="student_academic_assignments",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="student_academic_assignments",
    )

    programme = models.ForeignKey(
        Programme,
        on_delete=models.SET_NULL,
        related_name="student_academic_assignments",
        blank=True,
        null=True,
    )

    admission_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    year_of_study = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ],
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "department__name",
            "student__full_name",
        ]

    def clean(self):
        errors = {}

        if (
            self.school_id
            and self.institution_id
            and self.school.institution_id != self.institution_id
        ):
            errors["school"] = (
                "The school/faculty must belong to the selected institution."
            )

        if (
            self.department_id
            and self.school_id
            and self.department.school_id != self.school_id
        ):
            errors["department"] = (
                "The department must belong to the selected school/faculty."
            )

        if (
            self.programme_id
            and self.department_id
            and self.programme.department_id != self.department_id
        ):
            errors["programme"] = (
                "The programme must belong to the selected department."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.department.name}"
        )


class SupervisorAcademicAssignment(models.Model):
    supervisor = models.OneToOneField(
        "supervisors.SupervisorProfile",
        on_delete=models.CASCADE,
        related_name="academic_assignment",
    )

    institution = models.ForeignKey(
        "institutions.InstitutionProfile",
        on_delete=models.CASCADE,
        related_name="supervisor_academic_assignments",
    )

    school = models.ForeignKey(
        SchoolFaculty,
        on_delete=models.CASCADE,
        related_name="supervisor_academic_assignments",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="supervisor_academic_assignments",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "department__name",
            "supervisor__full_name",
        ]

    def clean(self):
        errors = {}

        if (
            self.school_id
            and self.institution_id
            and self.school.institution_id != self.institution_id
        ):
            errors["school"] = (
                "The school/faculty must belong to the selected institution."
            )

        if (
            self.department_id
            and self.school_id
            and self.department.school_id != self.school_id
        ):
            errors["department"] = (
                "The department must belong to the selected school/faculty."
            )

        if (
            self.supervisor_id
            and self.supervisor.institution_id
            and self.supervisor.institution_id != self.institution_id
        ):
            errors["supervisor"] = (
                "The supervisor belongs to a different institution."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        update_fields = []

        if self.supervisor.institution_id != self.institution_id:
            self.supervisor.institution = self.institution
            update_fields.append("institution")

        if self.supervisor.department != self.department.name:
            self.supervisor.department = self.department.name
            update_fields.append("department")

        if update_fields:
            self.supervisor.save(update_fields=update_fields)

    def __str__(self):
        return (
            f"{self.supervisor} - "
            f"{self.department.name}"
        )


class GradeScale(models.Model):
    institution = models.ForeignKey(
        "institutions.InstitutionProfile",
        on_delete=models.CASCADE,
        related_name="grade_scales",
    )
    name = models.CharField(max_length=120)
    coursework_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Maximum CAT/coursework mark, for example 30.",
    )
    examination_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Maximum examination mark, for example 70.",
    )
    pass_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="academic_grade_scales_created",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["institution__institution_name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_grade_scale_name_per_institution",
            )
        ]

    def clean(self):
        errors = {}

        if (
            self.coursework_weight is not None
            and self.examination_weight is not None
            and self.coursework_weight + self.examination_weight != 100
        ):
            errors["examination_weight"] = (
                "Coursework and examination weights must total 100."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        if self.is_default:
            GradeScale.objects.filter(
                institution=self.institution,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)

    def resolve_band(self, mark):
        if mark is None:
            return None

        return self.bands.filter(
            minimum_mark__lte=mark,
            maximum_mark__gte=mark,
        ).order_by("-minimum_mark").first()

    def __str__(self):
        return f"{self.name} - {self.institution.institution_name}"


class GradeBand(models.Model):
    scale = models.ForeignKey(
        GradeScale,
        on_delete=models.CASCADE,
        related_name="bands",
    )
    minimum_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    maximum_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    letter_grade = models.CharField(max_length=10)
    grade_point = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    remark = models.CharField(max_length=80, blank=True, default="")
    is_pass = models.BooleanField(default=True)

    class Meta:
        ordering = ["scale", "-minimum_mark"]
        constraints = [
            models.UniqueConstraint(
                fields=["scale", "letter_grade"],
                name="unique_letter_grade_per_scale",
            )
        ]

    def clean(self):
        errors = {}

        if (
            self.minimum_mark is not None
            and self.maximum_mark is not None
            and self.minimum_mark > self.maximum_mark
        ):
            errors["maximum_mark"] = (
                "Maximum mark cannot be lower than minimum mark."
            )

        if self.scale_id and self.minimum_mark is not None and self.maximum_mark is not None:
            overlapping = GradeBand.objects.filter(
                scale_id=self.scale_id,
                minimum_mark__lte=self.maximum_mark,
                maximum_mark__gte=self.minimum_mark,
            ).exclude(pk=self.pk)

            if overlapping.exists():
                errors["minimum_mark"] = (
                    "This range overlaps another grade band in the scale."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.letter_grade = self.letter_grade.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.letter_grade}: "
            f"{self.minimum_mark}-{self.maximum_mark}"
        )


class StudentUnitRegistration(models.Model):
    assignment = models.ForeignKey(
        StudentAcademicAssignment,
        on_delete=models.CASCADE,
        related_name="unit_registrations",
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="student_registrations",
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        related_name="student_unit_registrations",
    )
    study_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="academic_unit_registrations_created",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "semester__academic_year__starts_on",
            "semester__number",
            "unit__code",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "unit", "semester"],
                name="unique_student_unit_registration",
            )
        ]

    def clean(self):
        errors = {}

        if self.assignment_id and self.unit_id:
            if not self.assignment.programme_id:
                errors["assignment"] = (
                    "The student must have a programme before unit registration."
                )
            elif self.unit.programme_id != self.assignment.programme_id:
                errors["unit"] = (
                    "The unit must belong to the student's programme."
                )

            if self.unit.year_of_study != self.study_year:
                errors["study_year"] = (
                    "Study year must match the unit's configured year."
                )

        if self.assignment_id and self.semester_id:
            if (
                self.semester.academic_year.institution_id
                != self.assignment.institution_id
            ):
                errors["semester"] = (
                    "The semester belongs to a different institution."
                )

            if self.unit_id and self.unit.semester_number != self.semester.number:
                errors["semester"] = (
                    "The unit is configured for a different semester number."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.assignment.student} - {self.unit.code}"


class SemesterResultSubmission(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("submitted", "Submitted to Dean"),
        ("returned", "Returned for Correction"),
        ("published", "Approved and Published"),
    )

    assignment = models.ForeignKey(
        StudentAcademicAssignment,
        on_delete=models.PROTECT,
        related_name="result_submissions",
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        related_name="result_submissions",
    )
    grading_scale = models.ForeignKey(
        GradeScale,
        on_delete=models.PROTECT,
        related_name="result_submissions",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="academic_results_submitted",
        blank=True,
        null=True,
    )
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="academic_results_reviewed",
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    review_notes = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-semester__academic_year__starts_on", "-semester__number"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "semester"],
                name="unique_student_semester_result_submission",
            )
        ]

    def clean(self):
        errors = {}

        if self.assignment_id and self.semester_id:
            if (
                self.semester.academic_year.institution_id
                != self.assignment.institution_id
            ):
                errors["semester"] = (
                    "The semester belongs to a different institution."
                )

        if self.assignment_id and self.grading_scale_id:
            if self.grading_scale.institution_id != self.assignment.institution_id:
                errors["grading_scale"] = (
                    "The grading scale belongs to a different institution."
                )

        if self.status == "submitted" and not self.submitted_by_id:
            errors["submitted_by"] = "Submitted results must record the HOD."

        if self.status == "published":
            if not self.reviewed_by_id:
                errors["reviewed_by"] = "Published results must record the Dean."
            if not self.published_at:
                errors["published_at"] = "Published results require a publication time."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_locked(self):
        return self.status in {"submitted", "published"}

    @property
    def student(self):
        return self.assignment.student

    def __str__(self):
        return f"{self.assignment.student} - {self.semester}"


class LecturerResultSheet(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("submitted", "Submitted to HOD"),
        ("approved", "Approved by HOD"),
        ("returned", "Returned for Correction"),
    )

    lecturer_assignment = models.OneToOneField(
        LecturerUnitAssignment,
        on_delete=models.PROTECT,
        related_name="result_sheet",
    )
    grading_scale = models.ForeignKey(
        GradeScale,
        on_delete=models.PROTECT,
        related_name="lecturer_result_sheets",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="lecturer_result_sheets_reviewed",
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    review_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "-lecturer_assignment__semester__academic_year__starts_on",
            "lecturer_assignment__unit__code",
        ]

    def clean(self):
        errors = {}

        if self.lecturer_assignment_id and self.grading_scale_id:
            institution_id = (
                self.lecturer_assignment.semester.academic_year.institution_id
            )
            if self.grading_scale.institution_id != institution_id:
                errors["grading_scale"] = (
                    "The grading scale must belong to the same institution."
                )

        if self.status in {"submitted", "approved"} and not self.submitted_at:
            errors["submitted_at"] = "A submitted result sheet requires a submission time."

        if self.status in {"approved", "returned"}:
            if not self.reviewed_by_id:
                errors["reviewed_by"] = "An HOD-reviewed sheet must record the reviewer."
            if not self.reviewed_at:
                errors["reviewed_at"] = "An HOD-reviewed sheet requires a review time."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_locked(self):
        return self.status in {"submitted", "approved"}

    def __str__(self):
        assignment = self.lecturer_assignment
        return f"{assignment.unit.code} - {assignment.semester}"


class LecturerResultSheetAuditLog(models.Model):
    ACTION_CHOICES = (
        ("created", "Sheet Created"),
        ("marks_saved", "Marks Saved"),
        ("submitted", "Submitted to HOD"),
        ("approved", "Approved by HOD"),
        ("returned", "Returned to Lecturer"),
    )

    sheet = models.ForeignKey(
        LecturerResultSheet,
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="lecturer_result_sheet_audit_actions",
        blank=True,
        null=True,
    )
    details = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.sheet}"


class StudentGrade(models.Model):
    registration = models.OneToOneField(
        StudentUnitRegistration,
        on_delete=models.PROTECT,
        related_name="grade",
    )
    submission = models.ForeignKey(
        SemesterResultSubmission,
        on_delete=models.PROTECT,
        related_name="grades",
    )
    lecturer_result_sheet = models.ForeignKey(
        LecturerResultSheet,
        on_delete=models.PROTECT,
        related_name="grades",
        blank=True,
        null=True,
    )
    coursework_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    examination_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    total_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        editable=False,
    )
    letter_grade = models.CharField(max_length=10, editable=False)
    grade_point = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        editable=False,
    )
    remark = models.CharField(max_length=80, blank=True, default="", editable=False)
    is_pass = models.BooleanField(default=False, editable=False)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="academic_grades_entered",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["registration__unit__code"]

    def clean(self):
        errors = {}

        if self.registration_id and self.submission_id:
            if (
                self.registration.assignment_id
                != self.submission.assignment_id
            ):
                errors["submission"] = (
                    "The grade submission belongs to a different student."
                )

            if self.registration.semester_id != self.submission.semester_id:
                errors["submission"] = (
                    "The grade submission belongs to a different semester."
                )

            scale = self.submission.grading_scale

            if (
                self.coursework_mark is not None
                and self.coursework_mark > scale.coursework_weight
            ):
                errors["coursework_mark"] = (
                    f"Coursework mark cannot exceed {scale.coursework_weight}."
                )

            if (
                self.examination_mark is not None
                and self.examination_mark > scale.examination_weight
            ):
                errors["examination_mark"] = (
                    f"Examination mark cannot exceed {scale.examination_weight}."
                )

        if self.registration_id and self.lecturer_result_sheet_id:
            lecturer_assignment = self.lecturer_result_sheet.lecturer_assignment

            if self.registration.unit_id != lecturer_assignment.unit_id:
                errors["lecturer_result_sheet"] = (
                    "The result sheet belongs to a different unit."
                )

            if self.registration.semester_id != lecturer_assignment.semester_id:
                errors["lecturer_result_sheet"] = (
                    "The result sheet belongs to a different semester."
                )

        if errors:
            raise ValidationError(errors)

    def calculate_outcome(self):
        if self.coursework_mark is None or self.examination_mark is None:
            raise ValidationError(
                "Both coursework and examination marks are required."
            )

        if not self.submission_id:
            raise ValidationError(
                {"submission": "Select a semester result submission."}
            )

        self.total_mark = self.coursework_mark + self.examination_mark
        band = self.submission.grading_scale.resolve_band(self.total_mark)

        if band is None:
            raise ValidationError(
                {
                    "total_mark": (
                        "No grade band covers this total mark. "
                        "Complete the institution's grading scale first."
                    )
                }
            )

        self.letter_grade = band.letter_grade
        self.grade_point = band.grade_point
        self.remark = band.remark
        self.is_pass = band.is_pass

    def save(self, *args, **kwargs):
        self.calculate_outcome()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def quality_points(self):
        return self.grade_point * self.registration.unit.credit_hours

    def __str__(self):
        return (
            f"{self.registration.assignment.student} - "
            f"{self.registration.unit.code}: {self.letter_grade}"
        )


class GradeAmendmentRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending Dean Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    grade = models.ForeignKey(
        StudentGrade,
        on_delete=models.PROTECT,
        related_name="amendment_requests",
    )
    proposed_coursework_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    proposed_examination_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="grade_amendments_requested",
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="grade_amendments_reviewed",
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    review_notes = models.TextField(blank=True, default="")
    applied_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-requested_at"]

    def clean(self):
        errors = {}

        if self.grade_id:
            scale = self.grade.submission.grading_scale

            if (
                self.proposed_coursework_mark is not None
                and self.proposed_coursework_mark > scale.coursework_weight
            ):
                errors["proposed_coursework_mark"] = (
                    f"Coursework mark cannot exceed {scale.coursework_weight}."
                )

            if (
                self.proposed_examination_mark is not None
                and self.proposed_examination_mark > scale.examination_weight
            ):
                errors["proposed_examination_mark"] = (
                    f"Examination mark cannot exceed {scale.examination_weight}."
                )

        if self.status in {"approved", "rejected"} and not self.reviewed_by_id:
            errors["reviewed_by"] = "A reviewed request must record the Dean."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Amendment for {self.grade}"


class GradeAuditLog(models.Model):
    ACTION_CHOICES = (
        ("created", "Grade Created"),
        ("updated", "Grade Updated"),
        ("submitted", "Results Submitted"),
        ("returned", "Results Returned"),
        ("published", "Results Published"),
        ("amended", "Published Grade Amended"),
    )

    grade = models.ForeignKey(
        StudentGrade,
        on_delete=models.PROTECT,
        related_name="audit_logs",
        blank=True,
        null=True,
    )
    submission = models.ForeignKey(
        SemesterResultSubmission,
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="academic_grade_audit_actions",
        blank=True,
        null=True,
    )
    old_data = models.JSONField(blank=True, default=dict)
    new_data = models.JSONField(blank=True, default=dict)
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.submission}"
