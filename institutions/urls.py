from django.urls import path

from . import views


urlpatterns = [

    path(
        "institution/dashboard/",
        views.institution_dashboard,
        name="institution_dashboard",
    ),

    path(
        "institution/profile/create/",
        views.create_institution_profile,
        name="create_institution_profile",
    ),

  path(
    "institution/placements/<int:assignment_id>/",
    views.placement_detail,
    name="institution_placement_detail",
),

path(
    "institution/placements/<int:assignment_id>/complete/",
    views.complete_placement,
    name="institution_complete_placement",
),

  path(
    "institution/reports/",
    views.institution_reports,
    name="institution_reports",
),

path(
    "institution/reports/export/",
    views.export_institution_report_csv,
    name="institution_reports_csv",
),

    path(
        "institution/profile/edit/",
        views.edit_institution_profile,
        name="edit_institution_profile",
    ),

    path(
        "institution/students/",
        views.institution_students,
        name="institution_students",
    ),

    path(
        "institution/students/add/",
        views.create_placement_assignment,
        name="create_placement_assignment",
    ),

    path(
        "institution/students/<int:assignment_id>/edit/",
        views.edit_placement_assignment,
        name="edit_placement_assignment",
    ),
]