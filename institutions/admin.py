from django.contrib import admin

from .models import (
    InstitutionDirectory,
    InstitutionProfile,
    PlacementAssignment,
    PlacementProgressReport,
    SupervisorEvaluation,
)


@admin.register(InstitutionDirectory)
class InstitutionDirectoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "institution_type",
        "county",
        "is_active",
        "created_at",
    )
    list_filter = (
        "institution_type",
        "county",
        "is_active",
    )
    search_fields = (
        "name",
        "county",
    )
    ordering = (
        "name",
    )


@admin.register(InstitutionProfile)
class InstitutionProfileAdmin(admin.ModelAdmin):

    list_display = (
        "institution_name",
        "institution_type",
        "official_email",
        "county",
        "town",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "institution_type",
        "is_verified",
        "county",
    )

    search_fields = (
        "institution_name",
        "registration_number",
        "official_email",
        "phone_number",
        "county",
        "town",
    )


@admin.register(PlacementAssignment)
class PlacementAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "institution",
        "supervisor",
        "status",
        "start_date",
        "end_date",
        "created_at",
    )

    list_filter = (
        "status",
        "institution",
        "supervisor",
    )

    search_fields = (
        "student__full_name",
        "student__user__username",
        "student__user__email",
        "institution__institution_name",
        "supervisor__full_name",
    )


@admin.register(PlacementProgressReport)
class PlacementProgressReportAdmin(admin.ModelAdmin):

    list_display = (
        "student_name",
        "week_number",
        "status",
        "hours_worked",
        "submitted_at",
        "reviewed_at",
    )

    list_filter = (
        "status",
        "week_number",
    )

    search_fields = (
        "assignment__student__full_name",
        "assignment__student__user__username",
        "assignment__student__user__email",
        "activities",
        "skills_gained",
    )

    def student_name(self, obj):
        return obj.assignment.student

    student_name.short_description = "Student"


@admin.register(SupervisorEvaluation)
class SupervisorEvaluationAdmin(admin.ModelAdmin):

    list_display = (
        "student_name",
        "supervisor",
        "evaluation_type",
        "average_score_display",
        "recommendation",
        "created_at",
    )

    list_filter = (
        "evaluation_type",
        "recommendation",
    )

    search_fields = (
        "assignment__student__full_name",
        "assignment__student__user__username",
        "supervisor__full_name",
    )

    def student_name(self, obj):
        return obj.assignment.student

    student_name.short_description = "Student"

    def average_score_display(self, obj):
        return f"{obj.average_score}/5"

    average_score_display.short_description = "Average"