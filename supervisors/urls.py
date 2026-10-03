from django.urls import path

from . import views


urlpatterns = [

    path(
        "supervisor/dashboard/",
        views.supervisor_dashboard,
        name="supervisor_dashboard",
    ),

    path(
        "supervisor/profile/create/",
        views.create_supervisor_profile,
        name="create_supervisor_profile",
    ),

    path(
        "supervisor/profile/edit/",
        views.edit_supervisor_profile,
        name="edit_supervisor_profile",
    ),

    path(
        "supervisor/students/",
        views.assigned_students,
        name="supervisor_assigned_students",
    ),

    path(
        "supervisor/students/<int:assignment_id>/",
        views.student_assignment_detail,
        name="supervisor_student_detail",
    ),

    path(
        "supervisor/students/<int:assignment_id>/update/",
        views.update_assignment_status,
        name="supervisor_update_assignment",
    ),

    path(
        "supervisor/reports/<int:report_id>/review/",
        views.review_progress_report,
        name="supervisor_review_report",
    ),

    path(
        "supervisor/students/<int:assignment_id>/evaluation/add/",
        views.create_supervisor_evaluation,
        name="supervisor_add_evaluation",
    ),

    path(
        "supervisor/evaluations/<int:evaluation_id>/edit/",
        views.edit_supervisor_evaluation,
        name="supervisor_edit_evaluation",
    ),
]
