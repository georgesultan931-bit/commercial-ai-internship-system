import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from internships.models import Application

from .models import (
    InstitutionProfile,
    PlacementAssignment,
    PlacementProgressReport,
    SupervisorEvaluation,
)
from .forms import InstitutionProfileForm, PlacementAssignmentForm

def _is_institution_user(user):
    return getattr(user, "role", "") == "institution"


def _get_institution_profile(user):
    return InstitutionProfile.objects.filter(
        user=user
    ).first()


@login_required
def institution_dashboard(request):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can access this dashboard."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        messages.warning(
            request,
            "Your institution account is still awaiting administrator approval."
        )
        return redirect("pending_approval")

    profile = _get_institution_profile(request.user)

    if profile is None:
        messages.info(
            request,
            "Please complete your institution profile to continue."
        )
        return redirect("create_institution_profile")

    assignments = (
        PlacementAssignment.objects
        .filter(institution=profile)
        .select_related(
            "student",
            "student__user",
            "supervisor",
            "application",
            "application__opportunity",
        )
    )

    context = {
        "profile": profile,

        "total_students": assignments.values(
            "student_id"
        ).distinct().count(),

        "total_supervisors": profile.supervisors.count(),

        "total_assignments": assignments.count(),

        "ongoing_assignments": assignments.filter(
            status="ongoing"
        ).count(),

        "completed_assignments": assignments.filter(
            status="completed"
        ).count(),

        "pending_assignments": assignments.filter(
            status="pending"
        ).count(),

        "recent_assignments": assignments[:5],

        # Platform-wide number only.
        # This is NOT institution-specific.
        "total_applications": Application.objects.count(),
    }

    return render(
        request,
        "institutions/dashboard.html",
        context,
    )


@login_required
def institution_students(request):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can access student management."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_institution_profile(request.user)

    if profile is None:
        return redirect("create_institution_profile")

    assignments = (
        PlacementAssignment.objects
        .filter(institution=profile)
        .select_related(
            "student",
            "student__user",
            "supervisor",
            "supervisor__user",
            "application",
            "application__opportunity",
            "application__opportunity__employer",
        )
    )

    search_query = request.GET.get(
        "q",
        ""
    ).strip()

    status_filter = request.GET.get(
        "status",
        ""
    ).strip()

    if search_query:
        assignments = assignments.filter(
            Q(student__full_name__icontains=search_query)
            | Q(student__user__username__icontains=search_query)
            | Q(student__user__email__icontains=search_query)
            | Q(student__course__icontains=search_query)
            | Q(supervisor__full_name__icontains=search_query)
            | Q(application__opportunity__title__icontains=search_query)
        )

    if status_filter:
        assignments = assignments.filter(
            status=status_filter
        )

    context = {
        "profile": profile,
        "assignments": assignments,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": PlacementAssignment.STATUS_CHOICES,
    }

    return render(
        request,
        "institutions/students.html",
        context,
    )


@login_required
def create_placement_assignment(request):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can create placement assignments."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_institution_profile(request.user)

    if profile is None:
        return redirect("create_institution_profile")

    if request.method == "POST":
        form = PlacementAssignmentForm(
            request.POST,
            institution=profile,
        )

        if form.is_valid():
            assignment = form.save(
                commit=False
            )

            assignment.institution = profile
            assignment.save()

            messages.success(
                request,
                "Student placement assignment created successfully."
            )

            return redirect(
                "institution_students"
            )

        messages.error(
            request,
            "Please correct the errors below."
        )

    else:
        form = PlacementAssignmentForm(
            institution=profile
        )

    return render(
        request,
        "institutions/assign_supervisor.html",
        {
            "form": form,
            "profile": profile,
            "page_title": "Add Student Placement",
            "submit_text": "Create Assignment",
        },
    )


@login_required
def edit_placement_assignment(
    request,
    assignment_id
):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can edit placement assignments."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_institution_profile(request.user)

    if profile is None:
        return redirect(
            "create_institution_profile"
        )

    assignment = get_object_or_404(
        PlacementAssignment,
        pk=assignment_id,
        institution=profile,
    )

    if request.method == "POST":
        form = PlacementAssignmentForm(
            request.POST,
            instance=assignment,
            institution=profile,
        )

        if form.is_valid():
            updated_assignment = form.save(
                commit=False
            )

            updated_assignment.institution = profile
            updated_assignment.save()

            messages.success(
                request,
                "Placement assignment updated successfully."
            )

            return redirect(
                "institution_students"
            )

        messages.error(
            request,
            "Please correct the errors below."
        )

    else:
        form = PlacementAssignmentForm(
            instance=assignment,
            institution=profile,
        )

    return render(
        request,
        "institutions/assign_supervisor.html",
        {
            "form": form,
            "profile": profile,
            "assignment": assignment,
            "page_title": "Edit Student Placement",
            "submit_text": "Save Changes",
        },
    )


@login_required
def create_institution_profile(request):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can create an institution profile."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        messages.warning(
            request,
            "Your institution account must be approved before you can create a profile."
        )
        return redirect("pending_approval")

    if InstitutionProfile.objects.filter(
        user=request.user
    ).exists():
        return redirect(
            "institution_dashboard"
        )

    if request.method == "POST":
        form = InstitutionProfileForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            profile = form.save(
                commit=False
            )

            profile.user = request.user

            if not profile.official_email:
                profile.official_email = (
                    request.user.email
                )

            if not profile.phone_number:
                profile.phone_number = (
                    request.user.phone_number
                    or ""
                )

            profile.save()

            messages.success(
                request,
                "Institution profile created successfully."
            )

            return redirect(
                "institution_dashboard"
            )

        messages.error(
            request,
            "Please correct the form errors below."
        )

    else:
        form = InstitutionProfileForm(
            initial={
                "official_email": request.user.email,
                "phone_number": request.user.phone_number,
            }
        )

    return render(
        request,
        "institutions/create_profile.html",
        {
            "form": form
        }
    )


@login_required
def edit_institution_profile(request):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can edit an institution profile."
        )
        return redirect("dashboard")

    profile = _get_institution_profile(
        request.user
    )

    if profile is None:
        return redirect(
            "create_institution_profile"
        )

    if request.method == "POST":
        form = InstitutionProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Institution profile updated successfully."
            )

            return redirect(
                "institution_dashboard"
            )

        messages.error(
            request,
            "Please correct the form errors below."
        )

    else:
        form = InstitutionProfileForm(
            instance=profile
        )

    return render(
        request,
        "institutions/edit_profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )

@login_required
def institution_reports(request):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can access institution reports."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_institution_profile(request.user)

    if profile is None:
        return redirect("create_institution_profile")

    assignments = (
        PlacementAssignment.objects
        .filter(institution=profile)
        .select_related(
            "student",
            "student__user",
            "supervisor",
            "application",
            "application__opportunity",
        )
    )

    total_assignments = assignments.count()

    pending_assignments = assignments.filter(
        status="pending"
    ).count()

    assigned_assignments = assignments.filter(
        status="assigned"
    ).count()

    ongoing_assignments = assignments.filter(
        status="ongoing"
    ).count()

    completed_assignments = assignments.filter(
        status="completed"
    ).count()

    suspended_assignments = assignments.filter(
        status="suspended"
    ).count()

    cancelled_assignments = assignments.filter(
        status="cancelled"
    ).count()

    total_students = assignments.values(
        "student_id"
    ).distinct().count()

    total_supervisors = assignments.exclude(
        supervisor__isnull=True
    ).values(
        "supervisor_id"
    ).distinct().count()

    progress_reports = (
        PlacementProgressReport.objects
        .filter(
            assignment__institution=profile
        )
        .select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
        )
    )

    total_reports = progress_reports.count()

    submitted_reports = progress_reports.filter(
        status="submitted"
    ).count()

    reviewed_reports = progress_reports.filter(
        status="reviewed"
    ).count()

    revision_reports = progress_reports.filter(
        status="revision_required"
    ).count()

    evaluations = (
        SupervisorEvaluation.objects
        .filter(
            assignment__institution=profile
        )
        .select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
            "supervisor",
        )
    )

    total_evaluations = evaluations.count()

    midterm_evaluations = evaluations.filter(
        evaluation_type="midterm"
    ).count()

    final_evaluations = evaluations.filter(
        evaluation_type="final"
    ).count()

    # Evaluation scores are Python properties,
    # so calculate the average safely here.
    evaluation_scores = [
        evaluation.average_score
        for evaluation in evaluations
    ]

    if evaluation_scores:
        average_evaluation_score = round(
            sum(evaluation_scores)
            / len(evaluation_scores),
            2,
        )
    else:
        average_evaluation_score = 0

    if total_assignments:
        completion_rate = round(
            (
                completed_assignments
                / total_assignments
            ) * 100,
            1,
        )
    else:
        completion_rate = 0

    recent_reports = progress_reports.order_by(
        "-submitted_at"
    )[:8]

    recent_evaluations = evaluations.order_by(
        "-created_at"
    )[:8]

    context = {
        "profile": profile,

        "total_assignments": total_assignments,
        "pending_assignments": pending_assignments,
        "assigned_assignments": assigned_assignments,
        "ongoing_assignments": ongoing_assignments,
        "completed_assignments": completed_assignments,
        "suspended_assignments": suspended_assignments,
        "cancelled_assignments": cancelled_assignments,

        "total_students": total_students,
        "total_supervisors": total_supervisors,

        "total_reports": total_reports,
        "submitted_reports": submitted_reports,
        "reviewed_reports": reviewed_reports,
        "revision_reports": revision_reports,

        "total_evaluations": total_evaluations,
        "midterm_evaluations": midterm_evaluations,
        "final_evaluations": final_evaluations,
        "average_evaluation_score": average_evaluation_score,

        "completion_rate": completion_rate,

        "recent_reports": recent_reports,
        "recent_evaluations": recent_evaluations,
    }

    return render(
        request,
        "institutions/reports.html",
        context,
    )


@login_required
def export_institution_report_csv(request):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can export institution reports."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_institution_profile(request.user)

    if profile is None:
        return redirect("create_institution_profile")

    assignments = (
        PlacementAssignment.objects
        .filter(institution=profile)
        .select_related(
            "student",
            "student__user",
            "supervisor",
            "application",
            "application__opportunity",
        )
    )

    response = HttpResponse(
        content_type="text/csv"
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; filename="institution_placement_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Student",
        "Email",
        "Course",
        "Supervisor",
        "Opportunity",
        "Status",
        "Start Date",
        "End Date",
        "Logbook Reports",
        "Evaluations",
    ])

    for assignment in assignments:
        student = assignment.student

        supervisor_name = (
            assignment.supervisor.full_name
            if assignment.supervisor
            else "Not Assigned"
        )

        opportunity_title = (
            assignment.application.opportunity.title
            if (
                assignment.application
                and assignment.application.opportunity
            )
            else "Not Linked"
        )

        writer.writerow([
            getattr(
                student,
                "full_name",
                student.user.username,
            ),
            student.user.email,
            getattr(
                student,
                "course",
                "",
            ),
            supervisor_name,
            opportunity_title,
            assignment.get_status_display(),
            assignment.start_date or "",
            assignment.end_date or "",
            assignment.progress_reports.count(),
            assignment.evaluations.count(),
        ])

    return response

@login_required
def placement_detail(request, assignment_id):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can view placement details."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_institution_profile(request.user)

    if profile is None:
        return redirect("create_institution_profile")

    assignment = get_object_or_404(
        PlacementAssignment.objects.select_related(
            "student",
            "student__user",
            "supervisor",
            "supervisor__user",
            "application",
            "application__opportunity",
            "application__opportunity__employer",
        ),
        pk=assignment_id,
        institution=profile,
    )

    progress_reports = (
        assignment.progress_reports
        .all()
        .order_by("week_number")
    )

    evaluations = (
        assignment.evaluations
        .select_related("supervisor")
        .all()
        .order_by("created_at")
    )

    total_reports = progress_reports.count()

    reviewed_reports = progress_reports.filter(
        status="reviewed"
    ).count()

    submitted_reports = progress_reports.filter(
        status="submitted"
    ).count()

    revision_required_reports = progress_reports.filter(
        status="revision_required"
    ).count()

    midterm_evaluation = evaluations.filter(
        evaluation_type="midterm"
    ).first()

    final_evaluation = evaluations.filter(
        evaluation_type="final"
    ).first()

    unresolved_reports = progress_reports.exclude(
        status="reviewed"
    ).count()

    ready_for_completion = (
        final_evaluation is not None
        and unresolved_reports == 0
    )

    context = {
        "profile": profile,
        "assignment": assignment,
        "progress_reports": progress_reports,
        "evaluations": evaluations,

        "total_reports": total_reports,
        "reviewed_reports": reviewed_reports,
        "submitted_reports": submitted_reports,
        "revision_required_reports": revision_required_reports,

        "midterm_evaluation": midterm_evaluation,
        "final_evaluation": final_evaluation,

        "unresolved_reports": unresolved_reports,
        "ready_for_completion": ready_for_completion,
    }

    return render(
        request,
        "institutions/placement_detail.html",
        context,
    )


@login_required
def complete_placement(request, assignment_id):
    if not _is_institution_user(request.user):
        messages.error(
            request,
            "Only institution accounts can complete placements."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_institution_profile(request.user)

    if profile is None:
        return redirect("create_institution_profile")

    assignment = get_object_or_404(
        PlacementAssignment,
        pk=assignment_id,
        institution=profile,
    )

    if request.method != "POST":
        return redirect(
            "institution_placement_detail",
            assignment_id=assignment.id,
        )

    final_evaluation_exists = (
        assignment.evaluations.filter(
            evaluation_type="final"
        ).exists()
    )

    unresolved_reports = (
        assignment.progress_reports
        .exclude(status="reviewed")
        .exists()
    )

    if not final_evaluation_exists:
        messages.error(
            request,
            "A final supervisor evaluation is required before completing this placement."
        )

        return redirect(
            "institution_placement_detail",
            assignment_id=assignment.id,
        )

    if unresolved_reports:
        messages.error(
            request,
            "All submitted logbook reports must be reviewed before this placement can be completed."
        )

        return redirect(
            "institution_placement_detail",
            assignment_id=assignment.id,
        )

    assignment.status = "completed"
    assignment.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Placement successfully marked as completed."
    )

    return redirect(
        "institution_placement_detail",
        assignment_id=assignment.id,
    )