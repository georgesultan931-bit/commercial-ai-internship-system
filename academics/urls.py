from django.urls import path

from . import result_views, views


app_name = "academics"


urlpatterns = [
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "students/",
        views.department_students,
        name="department_students",
    ),
    path(
        "supervisors/",
        views.department_supervisors,
        name="department_supervisors",
    ),
    path(
        "applications/",
        views.department_applications,
        name="department_applications",
    ),
    path(
        "internships/",
        views.department_internships,
        name="department_internships",
    ),
    path(
        "reports/",
        views.academic_reports,
        name="academic_reports",
    ),
    path(
        "school/departments/",
        views.school_departments,
        name="school_departments",
    ),
    path(
        "school/students/",
        views.school_students,
        name="school_students",
    ),
    path(
        "school/supervisors/",
        views.school_supervisors,
        name="school_supervisors",
    ),
    path(
        "school/internships/",
        views.school_internships,
        name="school_internships",
    ),
    path(
        "school/applications/",
        views.school_applications,
        name="school_applications",
    ),

    # Lecturer unit-mark entry and submission workflow.
    path(
        "results/lecturer/",
        result_views.lecturer_result_dashboard,
        name="lecturer_result_dashboard",
    ),
    path(
        "results/lecturer/assignments/<int:assignment_id>/",
        result_views.lecturer_result_sheet,
        name="lecturer_result_sheet",
    ),
    path(
        "results/lecturer/sheets/<int:sheet_id>/submit/",
        result_views.submit_lecturer_result_sheet,
        name="submit_lecturer_result_sheet",
    ),

    # HOD academic-results workflow.
    path(
        "results/hod/students/",
        result_views.hod_result_students,
        name="hod_result_students",
    ),
    path(
        "results/hod/students/<int:assignment_id>/",
        result_views.hod_student_results,
        name="hod_student_results",
    ),
    path(
        "results/hod/submissions/<int:submission_id>/units/",
        result_views.register_student_units,
        name="register_student_units",
    ),
    path(
        "results/hod/submissions/<int:submission_id>/grades/",
        result_views.hod_result_entry,
        name="hod_result_entry",
    ),
    path(
        "results/hod/submissions/<int:submission_id>/submit/",
        result_views.submit_results_to_dean,
        name="submit_results_to_dean",
    ),
    path(
        "results/hod/grades/<int:grade_id>/amendment/",
        result_views.request_grade_amendment,
        name="request_grade_amendment",
    ),
    path(
        "results/hod/lecturer-sheets/",
        result_views.hod_lecturer_sheet_queue,
        name="hod_lecturer_sheet_queue",
    ),
    path(
        "results/hod/lecturer-sheets/<int:sheet_id>/review/",
        result_views.hod_review_lecturer_sheet,
        name="hod_review_lecturer_sheet",
    ),

    # Dean review, publication and amendment workflow.
    path(
        "results/dean/",
        result_views.dean_result_queue,
        name="dean_result_queue",
    ),
    path(
        "results/dean/submissions/<int:submission_id>/review/",
        result_views.dean_review_results,
        name="dean_review_results",
    ),
    path(
        "results/dean/amendments/",
        result_views.dean_amendment_queue,
        name="dean_amendment_queue",
    ),
    path(
        "results/dean/amendments/<int:amendment_id>/review/",
        result_views.dean_review_amendment,
        name="dean_review_amendment",
    ),

    # Published student results and official downloads.
    path(
        "results/my/",
        result_views.my_academic_results,
        name="my_academic_results",
    ),
    path(
        "results/my/<int:submission_id>/result-slip/",
        result_views.download_result_slip,
        name="download_result_slip",
    ),
    path(
        "results/my/transcript/",
        result_views.download_transcript,
        name="download_transcript",
    ),
]
