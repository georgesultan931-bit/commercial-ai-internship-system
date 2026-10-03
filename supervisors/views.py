from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from institutions.models import (
    PlacementAssignment,
    PlacementProgressReport,
    SupervisorEvaluation,
)

from .forms import (
    ProgressReportReviewForm,
    SupervisorEvaluationForm,
    SupervisorProfileForm,
)
from .models import SupervisorProfile


def _is_supervisor_user(user):
    return getattr(user, "role", "") == "supervisor"


def _get_supervisor_profile(user):
    return (
        SupervisorProfile.objects
        .select_related("institution")
        .filter(user=user)
        .first()
    )


@login_required
def supervisor_dashboard(request):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can access this dashboard."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        messages.warning(
            request,
            "Your supervisor account is still awaiting administrator approval."
        )
        return redirect("pending_approval")

    profile = _get_supervisor_profile(request.user)

    if profile is None:
        messages.info(
            request,
            "Please complete your supervisor profile to continue."
        )
        return redirect("create_supervisor_profile")

    assignments = (
        PlacementAssignment.objects
        .filter(supervisor=profile)
        .select_related(
            "student",
            "student__user",
            "institution",
            "application",
            "application__opportunity",
            "application__opportunity__employer",
        )
    )

    context = {
        "profile": profile,
        "total_students": assignments.values(
            "student_id"
        ).distinct().count(),
        "total_assignments": assignments.count(),
        "pending_assignments": assignments.filter(
            status="pending"
        ).count(),
        "assigned_assignments": assignments.filter(
            status="assigned"
        ).count(),
        "ongoing_assignments": assignments.filter(
            status="ongoing"
        ).count(),
        "completed_assignments": assignments.filter(
            status="completed"
        ).count(),
        "recent_assignments": assignments[:5],
    }

    return render(
        request,
        "supervisors/dashboard.html",
        context,
    )


@login_required
def assigned_students(request):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can access assigned students."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_supervisor_profile(request.user)

    if profile is None:
        return redirect("create_supervisor_profile")

    assignments = (
        PlacementAssignment.objects
        .filter(supervisor=profile)
        .select_related(
            "student",
            "student__user",
            "institution",
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
            | Q(application__opportunity__title__icontains=search_query)
            | Q(
                application__opportunity__employer__company_name__icontains=
                search_query
            )
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
        "supervisors/assigned_students.html",
        context,
    )


@login_required
def student_assignment_detail(request, assignment_id):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can view assigned student details."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_supervisor_profile(request.user)

    if profile is None:
        return redirect("create_supervisor_profile")

    assignment = get_object_or_404(
        PlacementAssignment.objects.select_related(
            "student",
            "student__user",
            "institution",
            "application",
            "application__opportunity",
            "application__opportunity__employer",
        ),
        pk=assignment_id,
        supervisor=profile,
    )

    progress_reports = assignment.progress_reports.all().order_by(
        "week_number",
        "submitted_at",
    )

    evaluations = assignment.evaluations.select_related(
        "supervisor"
    ).all().order_by("created_at")

    return render(
        request,
        "supervisors/student_detail.html",
        {
            "profile": profile,
            "assignment": assignment,
            "progress_reports": progress_reports,
            "evaluations": evaluations,
            "reviewed_reports": progress_reports.filter(status="reviewed").count(),
            "submitted_reports": progress_reports.filter(status="submitted").count(),
            "revision_required_reports": progress_reports.filter(
                status="revision_required"
            ).count(),
            "has_midterm_evaluation": evaluations.filter(
                evaluation_type="midterm"
            ).exists(),
            "has_final_evaluation": evaluations.filter(
                evaluation_type="final"
            ).exists(),
        },
    )


@login_required
def update_assignment_status(request, assignment_id):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can update assigned placements."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_supervisor_profile(request.user)

    if profile is None:
        return redirect("create_supervisor_profile")

    assignment = get_object_or_404(
        PlacementAssignment,
        pk=assignment_id,
        supervisor=profile,
    )

    if request.method != "POST":
        return redirect(
            "supervisor_student_detail",
            assignment_id=assignment.id,
        )

    allowed_statuses = {
        "assigned",
        "ongoing",
        "completed",
    }

    new_status = request.POST.get(
        "status",
        ""
    ).strip()

    supervisor_notes = request.POST.get(
        "supervisor_notes",
        ""
    ).strip()

    if new_status not in allowed_statuses:
        messages.error(
            request,
            "Please select a valid placement status."
        )

        return redirect(
            "supervisor_student_detail",
            assignment_id=assignment.id,
        )

    assignment.status = new_status
    assignment.supervisor_notes = supervisor_notes

    assignment.save(
        update_fields=[
            "status",
            "supervisor_notes",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Student placement progress updated successfully."
    )

    return redirect(
        "supervisor_student_detail",
        assignment_id=assignment.id,
    )


@login_required
def review_progress_report(request, report_id):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can review progress reports."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_supervisor_profile(request.user)

    if profile is None:
        return redirect("create_supervisor_profile")

    report = get_object_or_404(
        PlacementProgressReport.objects.select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
        ),
        pk=report_id,
        assignment__supervisor=profile,
    )

    if request.method == "POST":
        form = ProgressReportReviewForm(
            request.POST,
            instance=report,
        )

        if form.is_valid():
            reviewed_report = form.save(commit=False)

            # Support the current model safely if audit fields are present.
            if hasattr(reviewed_report, "reviewed_by"):
                reviewed_report.reviewed_by = profile

            if hasattr(reviewed_report, "reviewed_at"):
                from django.utils import timezone
                reviewed_report.reviewed_at = timezone.now()

            reviewed_report.save()

            messages.success(
                request,
                f"Week {reviewed_report.week_number} report reviewed successfully."
            )

            return redirect(
                "supervisor_student_detail",
                assignment_id=report.assignment_id,
            )

        messages.error(
            request,
            "Please correct the report review form errors."
        )

    else:
        form = ProgressReportReviewForm(instance=report)

    return render(
        request,
        "supervisors/review_progress_report.html",
        {
            "profile": profile,
            "report": report,
            "assignment": report.assignment,
            "form": form,
        },
    )


@login_required
def create_supervisor_evaluation(request, assignment_id):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can create evaluations."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_supervisor_profile(request.user)

    if profile is None:
        return redirect("create_supervisor_profile")

    assignment = get_object_or_404(
        PlacementAssignment.objects.select_related(
            "student",
            "student__user",
            "institution",
        ),
        pk=assignment_id,
        supervisor=profile,
    )

    if request.method == "POST":
        form = SupervisorEvaluationForm(request.POST)

        if form.is_valid():
            evaluation_type = form.cleaned_data.get("evaluation_type")

            if assignment.evaluations.filter(
                evaluation_type=evaluation_type
            ).exists():
                messages.error(
                    request,
                    f"A {evaluation_type} evaluation already exists for this placement."
                )
            else:
                evaluation = form.save(commit=False)
                evaluation.assignment = assignment
                evaluation.supervisor = profile
                evaluation.save()

                messages.success(
                    request,
                    f"{evaluation.get_evaluation_type_display()} evaluation saved successfully."
                )

                return redirect(
                    "supervisor_student_detail",
                    assignment_id=assignment.id,
                )

        else:
            messages.error(
                request,
                "Please correct the evaluation form errors."
            )

    else:
        form = SupervisorEvaluationForm()

    return render(
        request,
        "supervisors/evaluation_form.html",
        {
            "profile": profile,
            "assignment": assignment,
            "form": form,
            "page_title": "Add Supervisor Evaluation",
        },
    )


@login_required
def edit_supervisor_evaluation(request, evaluation_id):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can edit evaluations."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        return redirect("pending_approval")

    profile = _get_supervisor_profile(request.user)

    if profile is None:
        return redirect("create_supervisor_profile")

    evaluation = get_object_or_404(
        SupervisorEvaluation.objects.select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
        ),
        pk=evaluation_id,
        supervisor=profile,
        assignment__supervisor=profile,
    )

    if request.method == "POST":
        form = SupervisorEvaluationForm(
            request.POST,
            instance=evaluation,
        )

        if form.is_valid():
            evaluation_type = form.cleaned_data.get("evaluation_type")

            duplicate_exists = (
                evaluation.assignment.evaluations
                .filter(evaluation_type=evaluation_type)
                .exclude(pk=evaluation.pk)
                .exists()
            )

            if duplicate_exists:
                messages.error(
                    request,
                    f"A {evaluation_type} evaluation already exists for this placement."
                )
            else:
                updated = form.save(commit=False)
                updated.assignment = evaluation.assignment
                updated.supervisor = profile
                updated.save()

                messages.success(
                    request,
                    "Supervisor evaluation updated successfully."
                )

                return redirect(
                    "supervisor_student_detail",
                    assignment_id=evaluation.assignment_id,
                )

        else:
            messages.error(
                request,
                "Please correct the evaluation form errors."
            )

    else:
        form = SupervisorEvaluationForm(instance=evaluation)

    return render(
        request,
        "supervisors/evaluation_form.html",
        {
            "profile": profile,
            "assignment": evaluation.assignment,
            "evaluation": evaluation,
            "form": form,
            "page_title": "Edit Supervisor Evaluation",
        },
    )


@login_required
def create_supervisor_profile(request):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can create a supervisor profile."
        )
        return redirect("dashboard")

    if not getattr(request.user, "is_approved", False):
        messages.warning(
            request,
            "Your supervisor account must be approved before you can create a profile."
        )
        return redirect("pending_approval")

    if SupervisorProfile.objects.filter(
        user=request.user
    ).exists():
        return redirect("supervisor_dashboard")

    if request.method == "POST":
        form = SupervisorProfileForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            profile = form.save(
                commit=False
            )

            profile.user = request.user

            if not profile.full_name:
                profile.full_name = (
                    request.user.get_full_name()
                    or request.user.username
                )

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
                "Supervisor profile created successfully."
            )

            return redirect(
                "supervisor_dashboard"
            )

        messages.error(
            request,
            "Please correct the form errors below."
        )

    else:
        form = SupervisorProfileForm(
            initial={
                "full_name": (
                    request.user.get_full_name()
                    or request.user.username
                ),
                "official_email": request.user.email,
                "phone_number": request.user.phone_number,
            }
        )

    return render(
        request,
        "supervisors/create_profile.html",
        {
            "form": form
        },
    )


@login_required
def edit_supervisor_profile(request):
    if not _is_supervisor_user(request.user):
        messages.error(
            request,
            "Only supervisor accounts can edit a supervisor profile."
        )
        return redirect("dashboard")

    profile = _get_supervisor_profile(
        request.user
    )

    if profile is None:
        return redirect(
            "create_supervisor_profile"
        )

    if request.method == "POST":
        form = SupervisorProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Supervisor profile updated successfully."
            )

            return redirect(
                "supervisor_dashboard"
            )

        messages.error(
            request,
            "Please correct the form errors below."
        )

    else:
        form = SupervisorProfileForm(
            instance=profile
        )

    return render(
        request,
        "supervisors/edit_profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )