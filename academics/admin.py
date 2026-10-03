from django.contrib import admin

from .models import (
    AcademicStaffProfile,
    AcademicYear,
    Department,
    GradeAmendmentRequest,
    GradeAuditLog,
    GradeBand,
    GradeScale,
    LecturerResultSheet,
    LecturerResultSheetAuditLog,
    LecturerUnitAssignment,
    Programme,
    SchoolFaculty,
    Semester,
    SemesterResultSubmission,
    StudentAcademicAssignment,
    StudentGrade,
    StudentUnitRegistration,
    SupervisorAcademicAssignment,
    Unit,
)


@admin.register(SchoolFaculty)
class SchoolFacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "institution", "is_active")
    list_filter = ("institution", "is_active")
    search_fields = ("name", "code", "institution__institution_name")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "school", "is_active")
    list_filter = ("school", "is_active")
    search_fields = ("name", "code", "school__name")


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "department",
        "qualification_level",
        "duration_years",
        "is_active",
    )
    list_filter = ("department", "qualification_level", "is_active")
    search_fields = ("name", "code", "department__name")


@admin.register(AcademicStaffProfile)
class AcademicStaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "academic_role",
        "institution",
        "school",
        "department",
        "staff_number",
        "is_active",
    )
    list_filter = ("academic_role", "institution", "school", "is_active")
    search_fields = (
        "user__username",
        "user__email",
        "staff_number",
        "job_title",
        "institution__institution_name",
        "school__name",
        "department__name",
    )
    autocomplete_fields = ("user",)
    list_select_related = ("user", "institution", "school", "department")


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "institution", "starts_on", "ends_on", "is_current")
    list_filter = ("institution", "is_current")
    search_fields = ("name", "institution__institution_name")


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "number",
        "academic_year",
        "starts_on",
        "ends_on",
        "is_current",
    )
    list_filter = ("academic_year", "is_current")
    search_fields = ("name", "academic_year__name")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "programme",
        "year_of_study",
        "semester_number",
        "credit_hours",
        "is_active",
    )
    list_filter = ("programme", "year_of_study", "semester_number", "is_active")
    search_fields = ("code", "title", "programme__name")


@admin.register(StudentAcademicAssignment)
class StudentAcademicAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "institution",
        "school",
        "department",
        "programme",
        "admission_number",
        "year_of_study",
        "is_active",
    )
    list_filter = (
        "institution",
        "school",
        "department",
        "programme",
        "year_of_study",
        "is_active",
    )
    search_fields = (
        "student__full_name",
        "student__user__username",
        "student__user__email",
        "admission_number",
        "programme__name",
        "department__name",
    )
    list_select_related = (
        "student",
        "student__user",
        "institution",
        "school",
        "department",
        "programme",
    )


@admin.register(SupervisorAcademicAssignment)
class SupervisorAcademicAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "supervisor",
        "institution",
        "school",
        "department",
        "is_active",
    )
    list_filter = ("institution", "school", "department", "is_active")
    search_fields = (
        "supervisor__full_name",
        "supervisor__user__username",
        "supervisor__official_email",
        "supervisor__staff_number",
        "department__name",
    )
    list_select_related = (
        "supervisor",
        "supervisor__user",
        "institution",
        "school",
        "department",
    )


class GradeBandInline(admin.TabularInline):
    model = GradeBand
    extra = 1
    fields = (
        "minimum_mark",
        "maximum_mark",
        "letter_grade",
        "grade_point",
        "remark",
        "is_pass",
    )
    ordering = ("-minimum_mark",)


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "institution",
        "coursework_weight",
        "examination_weight",
        "pass_mark",
        "is_default",
        "is_active",
    )
    list_filter = ("institution", "is_default", "is_active")
    search_fields = ("name", "institution__institution_name")
    readonly_fields = ("created_at", "updated_at")
    inlines = (GradeBandInline,)

    def save_model(self, request, obj, form, change):
        if obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GradeBand)
class GradeBandAdmin(admin.ModelAdmin):
    list_display = (
        "letter_grade",
        "scale",
        "minimum_mark",
        "maximum_mark",
        "grade_point",
        "is_pass",
    )
    list_filter = ("scale__institution", "scale", "is_pass")
    search_fields = ("letter_grade", "remark", "scale__name")
    list_select_related = ("scale", "scale__institution")


@admin.register(StudentUnitRegistration)
class StudentUnitRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "unit",
        "semester",
        "study_year",
        "is_active",
        "registered_at",
    )
    list_filter = (
        "assignment__institution",
        "assignment__school",
        "assignment__department",
        "semester",
        "study_year",
        "is_active",
    )
    search_fields = (
        "assignment__student__full_name",
        "assignment__admission_number",
        "unit__code",
        "unit__title",
    )
    list_select_related = (
        "assignment",
        "assignment__student",
        "unit",
        "semester",
        "registered_by",
    )
    readonly_fields = ("registered_at", "updated_at")


@admin.register(SemesterResultSubmission)
class SemesterResultSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "semester",
        "status",
        "grading_scale",
        "submitted_by",
        "submitted_at",
        "reviewed_by",
        "published_at",
    )
    list_filter = (
        "assignment__institution",
        "assignment__school",
        "assignment__department",
        "semester",
        "status",
    )
    search_fields = (
        "assignment__student__full_name",
        "assignment__admission_number",
        "assignment__programme__name",
    )
    list_select_related = (
        "assignment",
        "assignment__student",
        "semester",
        "grading_scale",
        "submitted_by",
        "reviewed_by",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "unit_code",
        "coursework_mark",
        "examination_mark",
        "total_mark",
        "letter_grade",
        "grade_point",
        "is_pass",
    )
    list_filter = (
        "submission__assignment__institution",
        "submission__assignment__school",
        "submission__assignment__department",
        "submission__semester",
        "letter_grade",
        "is_pass",
    )
    search_fields = (
        "submission__assignment__student__full_name",
        "submission__assignment__admission_number",
        "registration__unit__code",
        "registration__unit__title",
    )
    list_select_related = (
        "submission",
        "submission__assignment",
        "submission__assignment__student",
        "registration",
        "registration__unit",
        "entered_by",
    )
    readonly_fields = (
        "total_mark",
        "letter_grade",
        "grade_point",
        "remark",
        "is_pass",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Student")
    def student_name(self, obj):
        return obj.submission.assignment.student

    @admin.display(description="Unit")
    def unit_code(self, obj):
        return obj.registration.unit.code


@admin.register(GradeAmendmentRequest)
class GradeAmendmentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "grade",
        "status",
        "requested_by",
        "requested_at",
        "reviewed_by",
        "reviewed_at",
        "applied_at",
    )
    list_filter = (
        "status",
        "grade__submission__assignment__institution",
        "grade__submission__assignment__school",
        "requested_at",
    )
    search_fields = (
        "grade__submission__assignment__student__full_name",
        "grade__submission__assignment__admission_number",
        "grade__registration__unit__code",
        "reason",
    )
    list_select_related = (
        "grade",
        "grade__submission",
        "grade__submission__assignment",
        "grade__registration",
        "grade__registration__unit",
        "requested_by",
        "reviewed_by",
    )
    readonly_fields = ("requested_at", "reviewed_at", "applied_at")


@admin.register(GradeAuditLog)
class GradeAuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "submission", "grade", "actor", "created_at")
    list_filter = (
        "action",
        "submission__assignment__institution",
        "submission__assignment__school",
        "created_at",
    )
    search_fields = (
        "submission__assignment__student__full_name",
        "submission__assignment__admission_number",
        "grade__registration__unit__code",
        "actor__username",
        "reason",
    )
    list_select_related = (
        "submission",
        "submission__assignment",
        "submission__assignment__student",
        "grade",
        "actor",
    )
    readonly_fields = (
        "grade",
        "submission",
        "action",
        "actor",
        "old_data",
        "new_data",
        "reason",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LecturerUnitAssignment)
class LecturerUnitAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "lecturer",
        "unit",
        "semester",
        "is_active",
        "assigned_by",
    )
    list_filter = (
        "lecturer__institution",
        "lecturer__department",
        "semester",
        "is_active",
    )
    search_fields = (
        "lecturer__user__username",
        "lecturer__user__email",
        "unit__code",
        "unit__title",
    )
    list_select_related = (
        "lecturer",
        "lecturer__user",
        "unit",
        "semester",
        "assigned_by",
    )


@admin.register(LecturerResultSheet)
class LecturerResultSheetAdmin(admin.ModelAdmin):
    list_display = (
        "lecturer_assignment",
        "status",
        "grading_scale",
        "submitted_at",
        "reviewed_by",
        "reviewed_at",
    )
    list_filter = (
        "status",
        "lecturer_assignment__lecturer__institution",
        "lecturer_assignment__lecturer__department",
        "lecturer_assignment__semester",
    )
    search_fields = (
        "lecturer_assignment__lecturer__user__username",
        "lecturer_assignment__unit__code",
        "lecturer_assignment__unit__title",
    )
    list_select_related = (
        "lecturer_assignment",
        "lecturer_assignment__lecturer",
        "lecturer_assignment__unit",
        "lecturer_assignment__semester",
        "grading_scale",
        "reviewed_by",
    )
    readonly_fields = (
        "submitted_at",
        "reviewed_at",
        "created_at",
        "updated_at",
    )


@admin.register(LecturerResultSheetAuditLog)
class LecturerResultSheetAuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "sheet", "actor", "created_at")
    list_filter = (
        "action",
        "sheet__lecturer_assignment__lecturer__institution",
        "created_at",
    )
    search_fields = (
        "sheet__lecturer_assignment__lecturer__user__username",
        "sheet__lecturer_assignment__unit__code",
        "actor__username",
    )
    list_select_related = (
        "sheet",
        "sheet__lecturer_assignment",
        "sheet__lecturer_assignment__lecturer",
        "sheet__lecturer_assignment__unit",
        "actor",
    )
    readonly_fields = ("sheet", "action", "actor", "details", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
