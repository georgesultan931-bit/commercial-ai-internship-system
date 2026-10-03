from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from notifications.models import Notification

from .forms import (
    DeanResultReviewForm,
    GradeAmendmentRequestForm,
    GradeAmendmentReviewForm,
    GradeEntryFormSet,
    HODLecturerSheetReviewForm,
    LecturerGradeEntryFormSet,
    LecturerSheetSubmissionForm,
    ResultSubmissionForm,
    SemesterSubmissionSetupForm,
    UnitRegistrationForm,
)
from .models import (
    AcademicStaffProfile,
    GradeAmendmentRequest,
    GradeAuditLog,
    GradeScale,
    LecturerResultSheet,
    LecturerResultSheetAuditLog,
    LecturerUnitAssignment,
    SemesterResultSubmission,
    StudentAcademicAssignment,
    StudentGrade,
    StudentUnitRegistration,
)


def _notify(user, message):
    if user is not None:
        Notification.objects.create(user=user, message=message)


def _academic_profile(user, role):
    profile = (
        AcademicStaffProfile.objects.select_related(
            "institution",
            "school",
            "department",
        )
        .filter(
            user=user,
            academic_role=role,
            is_active=True,
        )
        .first()
    )

    if profile is None:
        raise PermissionDenied("No active academic staff assignment was found.")

    return profile


def _hod_profile(user):
    if getattr(user, "role", "") != "hod":
        raise PermissionDenied("Only a Head of Department can manage grades.")

    profile = _academic_profile(user, "hod")

    if not profile.department_id:
        raise PermissionDenied("Your HOD account has no assigned department.")

    return profile


def _lecturer_profile(user):
    if getattr(user, "role", "") != "lecturer":
        raise PermissionDenied("Only a Lecturer can enter assigned unit marks.")

    profile = _academic_profile(user, "lecturer")

    if not profile.department_id:
        raise PermissionDenied("Your Lecturer account has no assigned department.")

    return profile


def _dean_profile(user):
    if getattr(user, "role", "") != "dean":
        raise PermissionDenied("Only a Dean can review academic results.")

    profile = _academic_profile(user, "dean")

    if not profile.school_id:
        raise PermissionDenied("Your Dean account has no assigned school.")

    return profile


def _hod_assignment_or_404(user, assignment_id):
    profile = _hod_profile(user)
    assignment = get_object_or_404(
        StudentAcademicAssignment.objects.select_related(
            "student",
            "student__user",
            "institution",
            "school",
            "department",
            "programme",
        ),
        pk=assignment_id,
        department=profile.department,
        institution=profile.institution,
        is_active=True,
    )
    return profile, assignment


def _hod_submission_or_404(user, submission_id):
    profile = _hod_profile(user)
    submission = get_object_or_404(
        SemesterResultSubmission.objects.select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
            "assignment__institution",
            "assignment__school",
            "assignment__department",
            "assignment__programme",
            "semester",
            "semester__academic_year",
            "grading_scale",
        ),
        pk=submission_id,
        assignment__department=profile.department,
        assignment__institution=profile.institution,
    )
    return profile, submission


def _dean_submission_or_404(user, submission_id):
    profile = _dean_profile(user)
    submission = get_object_or_404(
        SemesterResultSubmission.objects.select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
            "assignment__institution",
            "assignment__school",
            "assignment__department",
            "assignment__programme",
            "semester",
            "semester__academic_year",
            "grading_scale",
            "submitted_by",
            "reviewed_by",
        ),
        pk=submission_id,
        assignment__school=profile.school,
        assignment__institution=profile.institution,
    )
    return profile, submission


def _grade_snapshot(grade):
    return {
        "coursework_mark": str(grade.coursework_mark),
        "examination_mark": str(grade.examination_mark),
        "total_mark": str(grade.total_mark),
        "letter_grade": grade.letter_grade,
        "grade_point": str(grade.grade_point),
        "remark": grade.remark,
        "is_pass": grade.is_pass,
    }


def _gpa(grades):
    credits = Decimal("0")
    quality_points = Decimal("0")

    for grade in grades:
        unit_credits = grade.registration.unit.credit_hours

        if unit_credits and unit_credits > 0:
            credits += unit_credits
            quality_points += grade.grade_point * unit_credits

    if credits == 0:
        return None

    return (quality_points / credits).quantize(Decimal("0.01"))


@login_required
def lecturer_result_dashboard(request):
    profile = _lecturer_profile(request.user)
    assignments = (
        LecturerUnitAssignment.objects.filter(
            lecturer=profile,
            is_active=True,
        )
        .select_related(
            "unit",
            "unit__programme",
            "semester",
            "semester__academic_year",
            "result_sheet",
        )
        .order_by(
            "-semester__academic_year__starts_on",
            "semester__number",
            "unit__code",
        )
    )

    return render(
        request,
        "academics/results/lecturer_dashboard.html",
        {"profile": profile, "assignments": assignments},
    )


@login_required
def lecturer_result_sheet(request, assignment_id):
    profile = _lecturer_profile(request.user)
    lecturer_assignment = get_object_or_404(
        LecturerUnitAssignment.objects.select_related(
            "unit",
            "unit__programme",
            "semester",
            "semester__academic_year",
            "lecturer",
        ),
        pk=assignment_id,
        lecturer=profile,
        is_active=True,
    )

    grading_scale = (
        GradeScale.objects.filter(
            institution=profile.institution,
            is_active=True,
            is_default=True,
        ).first()
        or GradeScale.objects.filter(
            institution=profile.institution,
            is_active=True,
        ).first()
    )

    if grading_scale is None:
        messages.error(
            request,
            "Your institution must configure an active grading scale first.",
        )
        return redirect("academics:lecturer_result_dashboard")

    sheet, sheet_created = LecturerResultSheet.objects.get_or_create(
        lecturer_assignment=lecturer_assignment,
        defaults={"grading_scale": grading_scale},
    )
    if sheet_created:
        LecturerResultSheetAuditLog.objects.create(
            sheet=sheet,
            action="created",
            actor=request.user,
        )
    grading_scale = sheet.grading_scale
    registrations = list(
        StudentUnitRegistration.objects.filter(
            unit=lecturer_assignment.unit,
            semester=lecturer_assignment.semester,
            assignment__institution=profile.institution,
            assignment__department=profile.department,
            assignment__is_active=True,
            is_active=True,
        )
        .select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
        )
        .order_by("assignment__admission_number", "assignment__student__full_name")
    )
    grades_by_registration = {
        grade.registration_id: grade
        for grade in StudentGrade.objects.filter(
            registration__in=registrations,
        ).select_related("submission")
    }
    editable = sheet.status in {"draft", "returned"}

    if request.method == "POST" and "save_marks" in request.POST:
        if not editable:
            messages.error(request, "Submitted or approved marks are locked.")
            return redirect(
                "academics:lecturer_result_sheet",
                assignment_id=lecturer_assignment.pk,
            )

        formset = LecturerGradeEntryFormSet(
            request.POST,
            prefix="grades",
            form_kwargs={
                "lecturer_assignment": lecturer_assignment,
                "grading_scale": grading_scale,
            },
        )

        if formset.is_valid():
            for form in formset:
                registration = form.registration
                existing_submission = SemesterResultSubmission.objects.filter(
                    assignment=registration.assignment,
                    semester=lecturer_assignment.semester,
                ).first()

                if existing_submission is None:
                    continue

                if existing_submission.status not in {"draft", "returned"}:
                    messages.error(
                        request,
                        (
                            f"{registration.assignment.student}'s results are "
                            "already locked for Dean processing."
                        ),
                    )
                    return redirect(
                        "academics:lecturer_result_sheet",
                        assignment_id=lecturer_assignment.pk,
                    )

                if existing_submission.grading_scale_id != grading_scale.pk:
                    messages.error(
                        request,
                        "A student's semester record uses a different grading scale.",
                    )
                    return redirect(
                        "academics:lecturer_result_sheet",
                        assignment_id=lecturer_assignment.pk,
                    )

            with transaction.atomic():
                for form in formset:
                    registration = form.registration
                    submission, _ = SemesterResultSubmission.objects.get_or_create(
                        assignment=registration.assignment,
                        semester=lecturer_assignment.semester,
                        defaults={
                            "grading_scale": grading_scale,
                            "status": "draft",
                        },
                    )

                    grade = grades_by_registration.get(registration.pk)
                    old_data = _grade_snapshot(grade) if grade else {}
                    action = "updated" if grade else "created"

                    if grade is None:
                        grade = StudentGrade(
                            registration=registration,
                            submission=submission,
                        )

                    grade.coursework_mark = form.cleaned_data["coursework_mark"]
                    grade.examination_mark = form.cleaned_data["examination_mark"]
                    grade.lecturer_result_sheet = sheet
                    grade.entered_by = request.user
                    grade.save()
                    GradeAuditLog.objects.create(
                        grade=grade,
                        submission=submission,
                        action=action,
                        actor=request.user,
                        old_data=old_data,
                        new_data=_grade_snapshot(grade),
                    )

                if sheet.status == "returned":
                    sheet.status = "draft"
                    sheet.save()

                LecturerResultSheetAuditLog.objects.create(
                    sheet=sheet,
                    action="marks_saved",
                    actor=request.user,
                    details={"student_count": len(registrations)},
                )

            messages.success(request, "Unit marks saved successfully.")
            return redirect(
                "academics:lecturer_result_sheet",
                assignment_id=lecturer_assignment.pk,
            )
    else:
        initial = []
        for registration in registrations:
            grade = grades_by_registration.get(registration.pk)
            initial.append(
                {
                    "registration_id": registration.pk,
                    "coursework_mark": (
                        grade.coursework_mark if grade else Decimal("0.00")
                    ),
                    "examination_mark": (
                        grade.examination_mark if grade else Decimal("0.00")
                    ),
                }
            )

        formset = LecturerGradeEntryFormSet(
            initial=initial,
            prefix="grades",
            form_kwargs={
                "lecturer_assignment": lecturer_assignment,
                "grading_scale": grading_scale,
            },
        )

    rows = list(zip(registrations, formset.forms))
    submission_form = LecturerSheetSubmissionForm(prefix="submit")
    graded_count = StudentGrade.objects.filter(
        registration__in=registrations,
        lecturer_result_sheet=sheet,
    ).count()

    return render(
        request,
        "academics/results/lecturer_result_sheet.html",
        {
            "profile": profile,
            "lecturer_assignment": lecturer_assignment,
            "sheet": sheet,
            "rows": rows,
            "formset": formset,
            "submission_form": submission_form,
            "editable": editable,
            "student_count": len(registrations),
            "graded_count": graded_count,
        },
    )


@login_required
def submit_lecturer_result_sheet(request, sheet_id):
    profile = _lecturer_profile(request.user)
    sheet = get_object_or_404(
        LecturerResultSheet.objects.select_related(
            "lecturer_assignment",
            "lecturer_assignment__unit",
            "lecturer_assignment__semester",
        ),
        pk=sheet_id,
        lecturer_assignment__lecturer=profile,
        lecturer_assignment__is_active=True,
    )

    if request.method != "POST":
        return redirect(
            "academics:lecturer_result_sheet",
            assignment_id=sheet.lecturer_assignment_id,
        )

    if sheet.status not in {"draft", "returned"}:
        messages.error(request, "This result sheet has already been submitted.")
        return redirect(
            "academics:lecturer_result_sheet",
            assignment_id=sheet.lecturer_assignment_id,
        )

    form = LecturerSheetSubmissionForm(request.POST, prefix="submit")
    registrations = StudentUnitRegistration.objects.filter(
        unit=sheet.lecturer_assignment.unit,
        semester=sheet.lecturer_assignment.semester,
        assignment__department=profile.department,
        assignment__institution=profile.institution,
        assignment__is_active=True,
        is_active=True,
    )
    registration_count = registrations.count()
    grade_count = StudentGrade.objects.filter(
        registration__in=registrations,
        lecturer_result_sheet=sheet,
    ).count()

    if registration_count == 0 or grade_count != registration_count:
        messages.error(
            request,
            "Every registered student must have CAT and examination marks.",
        )
        return redirect(
            "academics:lecturer_result_sheet",
            assignment_id=sheet.lecturer_assignment_id,
        )

    if form.is_valid():
        sheet.status = "submitted"
        sheet.submitted_at = timezone.now()
        sheet.reviewed_by = None
        sheet.reviewed_at = None
        sheet.review_notes = ""
        sheet.save()
        LecturerResultSheetAuditLog.objects.create(
            sheet=sheet,
            action="submitted",
            actor=request.user,
            details={"grade_count": grade_count},
        )

        hod_profiles = AcademicStaffProfile.objects.filter(
            institution=profile.institution,
            department=profile.department,
            academic_role="hod",
            is_active=True,
        ).select_related("user")

        for hod_profile in hod_profiles:
            _notify(
                hod_profile.user,
                (
                    f"{request.user.get_full_name() or request.user.username} "
                    f"submitted {sheet.lecturer_assignment.unit.code} marks for review."
                ),
            )

        messages.success(request, "Unit marks submitted to the HOD.")

    return redirect(
        "academics:lecturer_result_sheet",
        assignment_id=sheet.lecturer_assignment_id,
    )


@login_required
def hod_lecturer_sheet_queue(request):
    profile = _hod_profile(request.user)
    status = request.GET.get("status", "submitted").strip()
    if status not in {"submitted", "approved", "returned", "all"}:
        status = "submitted"

    sheets = (
        LecturerResultSheet.objects.filter(
            lecturer_assignment__lecturer__institution=profile.institution,
            lecturer_assignment__unit__programme__department=profile.department,
        )
        .select_related(
            "lecturer_assignment",
            "lecturer_assignment__lecturer",
            "lecturer_assignment__lecturer__user",
            "lecturer_assignment__unit",
            "lecturer_assignment__semester",
            "lecturer_assignment__semester__academic_year",
        )
        .order_by("-submitted_at", "lecturer_assignment__unit__code")
    )

    if status != "all":
        sheets = sheets.filter(status=status)

    counts = {
        key: LecturerResultSheet.objects.filter(
            lecturer_assignment__lecturer__institution=profile.institution,
            lecturer_assignment__unit__programme__department=profile.department,
            status=key,
        ).count()
        for key in ("submitted", "approved", "returned")
    }

    return render(
        request,
        "academics/results/hod_lecturer_sheets.html",
        {
            "profile": profile,
            "sheets": sheets,
            "selected_status": status,
            "counts": counts,
        },
    )


@login_required
def hod_review_lecturer_sheet(request, sheet_id):
    profile = _hod_profile(request.user)
    sheet = get_object_or_404(
        LecturerResultSheet.objects.select_related(
            "lecturer_assignment",
            "lecturer_assignment__lecturer",
            "lecturer_assignment__lecturer__user",
            "lecturer_assignment__unit",
            "lecturer_assignment__semester",
            "lecturer_assignment__semester__academic_year",
        ),
        pk=sheet_id,
        lecturer_assignment__lecturer__institution=profile.institution,
        lecturer_assignment__unit__programme__department=profile.department,
    )
    grades = list(
        sheet.grades.select_related(
            "registration",
            "registration__assignment",
            "registration__assignment__student",
        ).order_by("registration__assignment__admission_number")
    )

    if request.method == "POST":
        form = HODLecturerSheetReviewForm(request.POST)

        if sheet.status != "submitted":
            messages.error(request, "Only submitted unit marks can be reviewed.")
            return redirect(
                "academics:hod_review_lecturer_sheet",
                sheet_id=sheet.pk,
            )

        if form.is_valid():
            action = form.cleaned_data["action"]
            notes = form.cleaned_data["review_notes"].strip()
            sheet.status = "approved" if action == "approve" else "returned"
            sheet.reviewed_by = request.user
            sheet.reviewed_at = timezone.now()
            sheet.review_notes = notes
            sheet.save()
            LecturerResultSheetAuditLog.objects.create(
                sheet=sheet,
                action=sheet.status,
                actor=request.user,
                details={"review_notes": notes},
            )

            if action == "approve":
                message = (
                    f"Your {sheet.lecturer_assignment.unit.code} marks were approved."
                )
                messages.success(request, "Unit marks approved.")
            else:
                message = (
                    f"Your {sheet.lecturer_assignment.unit.code} marks were returned: "
                    f"{notes}"
                )
                messages.success(request, "Unit marks returned to the Lecturer.")

            _notify(sheet.lecturer_assignment.lecturer.user, message)
            return redirect("academics:hod_lecturer_sheet_queue")
    else:
        form = HODLecturerSheetReviewForm()

    return render(
        request,
        "academics/results/hod_review_lecturer_sheet.html",
        {
            "profile": profile,
            "sheet": sheet,
            "grades": grades,
            "form": form,
        },
    )


@login_required
def hod_result_students(request):
    profile = _hod_profile(request.user)
    query = request.GET.get("q", "").strip()

    assignments = (
        StudentAcademicAssignment.objects.filter(
            institution=profile.institution,
            department=profile.department,
            is_active=True,
        )
        .select_related("student", "student__user", "programme")
        .order_by("student__full_name", "admission_number")
    )

    if query:
        assignments = assignments.filter(
            Q(student__full_name__icontains=query)
            | Q(student__user__username__icontains=query)
            | Q(student__user__email__icontains=query)
            | Q(admission_number__icontains=query)
            | Q(programme__name__icontains=query)
        )

    return render(
        request,
        "academics/results/hod_students.html",
        {
            "profile": profile,
            "assignments": assignments,
            "query": query,
        },
    )


@login_required
def hod_student_results(request, assignment_id):
    profile, assignment = _hod_assignment_or_404(request.user, assignment_id)
    scales = GradeScale.objects.filter(
        institution=profile.institution,
        is_active=True,
    )

    setup_form = SemesterSubmissionSetupForm(
        request.POST or None,
        assignment=assignment,
        prefix="setup",
    )

    if request.method == "POST" and request.POST.get("form_action") == "setup":
        if not scales.exists():
            messages.error(
                request,
                "No active grading scale exists. Ask the Dean or administrator to configure one.",
            )
        elif setup_form.is_valid():
            semester = setup_form.cleaned_data["semester"]
            grading_scale = setup_form.cleaned_data["grading_scale"]
            submission, created = SemesterResultSubmission.objects.get_or_create(
                assignment=assignment,
                semester=semester,
                defaults={"grading_scale": grading_scale},
            )

            if not created and submission.status in {"draft", "returned"}:
                submission.grading_scale = grading_scale
                submission.save(update_fields=["grading_scale", "updated_at"])

            return redirect("academics:hod_result_entry", submission_id=submission.pk)

    submissions = (
        SemesterResultSubmission.objects.filter(assignment=assignment)
        .select_related(
            "semester",
            "semester__academic_year",
            "grading_scale",
            "submitted_by",
            "reviewed_by",
        )
        .prefetch_related("grades")
    )

    return render(
        request,
        "academics/results/hod_student_results.html",
        {
            "profile": profile,
            "assignment": assignment,
            "setup_form": setup_form,
            "submissions": submissions,
            "has_grading_scale": scales.exists(),
        },
    )


@login_required
def register_student_units(request, submission_id):
    profile, submission = _hod_submission_or_404(request.user, submission_id)

    if submission.status not in {"draft", "returned"}:
        messages.error(request, "Submitted or published results cannot be edited.")
        return redirect("academics:hod_result_entry", submission_id=submission.pk)

    if request.method == "POST":
        form = UnitRegistrationForm(
            request.POST,
            assignment=submission.assignment,
        )

        if form.is_valid():
            if form.cleaned_data["semester"].pk != submission.semester_id:
                form.add_error(
                    "semester",
                    "Select the same semester as this result submission.",
                )
            else:
                selected_units = form.cleaned_data["units"]
                study_year = form.cleaned_data["study_year"]

                with transaction.atomic():
                    for unit in selected_units:
                        StudentUnitRegistration.objects.get_or_create(
                            assignment=submission.assignment,
                            unit=unit,
                            semester=submission.semester,
                            defaults={
                                "study_year": study_year,
                                "registered_by": request.user,
                            },
                        )

                messages.success(request, "Student units registered successfully.")
                return redirect(
                    "academics:hod_result_entry",
                    submission_id=submission.pk,
                )
    else:
        form = UnitRegistrationForm(
            assignment=submission.assignment,
            initial={
                "semester": submission.semester,
                "study_year": submission.assignment.year_of_study,
            },
        )

    return render(
        request,
        "academics/results/register_units.html",
        {
            "profile": profile,
            "submission": submission,
            "form": form,
        },
    )


@login_required
def hod_result_entry(request, submission_id):
    profile, submission = _hod_submission_or_404(request.user, submission_id)
    registrations = list(
        StudentUnitRegistration.objects.filter(
            assignment=submission.assignment,
            semester=submission.semester,
            is_active=True,
        )
        .select_related("unit")
        .order_by("unit__code")
    )

    existing_grades = {
        grade.registration_id: grade
        for grade in StudentGrade.objects.filter(
            submission=submission,
        ).select_related("registration", "registration__unit")
    }

    initial = []

    for registration in registrations:
        grade = existing_grades.get(registration.pk)
        initial.append(
            {
                "registration_id": registration.pk,
                "coursework_mark": grade.coursework_mark if grade else None,
                "examination_mark": grade.examination_mark if grade else None,
            }
        )

    editable = submission.status in {"draft", "returned"}

    if request.method == "POST" and request.POST.get("form_action") == "save_grades":
        if not editable:
            messages.error(request, "These results are locked and cannot be edited.")
            return redirect("academics:hod_result_entry", submission_id=submission.pk)

        grade_formset = GradeEntryFormSet(
            request.POST,
            initial=initial,
            prefix="grades",
            form_kwargs={"submission": submission},
        )

        if grade_formset.is_valid():
            with transaction.atomic():
                for form in grade_formset:
                    registration = form.registration
                    old_grade = existing_grades.get(registration.pk)
                    old_data = _grade_snapshot(old_grade) if old_grade else {}
                    grade = existing_grades.get(registration.pk)
                    created = grade is None

                    if grade is None:
                        grade = StudentGrade(
                            registration=registration,
                            submission=submission,
                        )

                    grade.coursework_mark = form.cleaned_data["coursework_mark"]
                    grade.examination_mark = form.cleaned_data["examination_mark"]
                    grade.entered_by = request.user
                    grade.save()
                    GradeAuditLog.objects.create(
                        grade=grade,
                        submission=submission,
                        action="created" if created else "updated",
                        actor=request.user,
                        old_data=old_data,
                        new_data=_grade_snapshot(grade),
                    )

            messages.success(request, "Draft grades saved successfully.")
            return redirect("academics:hod_result_entry", submission_id=submission.pk)
    else:
        grade_formset = GradeEntryFormSet(
            initial=initial,
            prefix="grades",
            form_kwargs={"submission": submission},
        )

    rows = list(zip(registrations, grade_formset.forms))
    submission_form = ResultSubmissionForm(prefix="submit")

    return render(
        request,
        "academics/results/hod_result_entry.html",
        {
            "profile": profile,
            "submission": submission,
            "rows": rows,
            "grade_formset": grade_formset,
            "submission_form": submission_form,
            "editable": editable,
            "registered_count": len(registrations),
            "graded_count": len(existing_grades),
        },
    )


@login_required
def submit_results_to_dean(request, submission_id):
    profile, submission = _hod_submission_or_404(request.user, submission_id)

    if request.method != "POST":
        return redirect("academics:hod_result_entry", submission_id=submission.pk)

    if submission.status not in {"draft", "returned"}:
        messages.error(request, "These results have already been submitted.")
        return redirect("academics:hod_result_entry", submission_id=submission.pk)

    form = ResultSubmissionForm(request.POST, prefix="submit")
    registration_count = StudentUnitRegistration.objects.filter(
        assignment=submission.assignment,
        semester=submission.semester,
        is_active=True,
    ).count()
    grade_count = submission.grades.count()

    if registration_count == 0 or grade_count != registration_count:
        messages.error(
            request,
            "Every registered unit must have CAT and examination marks before submission.",
        )
        return redirect("academics:hod_result_entry", submission_id=submission.pk)

    unapproved_lecturer_units = []
    for grade in submission.grades.select_related(
        "registration",
        "registration__unit",
        "lecturer_result_sheet",
    ):
        has_lecturer_assignment = LecturerUnitAssignment.objects.filter(
            unit=grade.registration.unit,
            semester=submission.semester,
            is_active=True,
        ).exists()

        if has_lecturer_assignment and (
            grade.lecturer_result_sheet_id is None
            or grade.lecturer_result_sheet.status != "approved"
        ):
            unapproved_lecturer_units.append(grade.registration.unit.code)

    if unapproved_lecturer_units:
        messages.error(
            request,
            (
                "These Lecturer marks require HOD approval first: "
                f"{', '.join(sorted(set(unapproved_lecturer_units)))}."
            ),
        )
        return redirect("academics:hod_result_entry", submission_id=submission.pk)

    if form.is_valid():
        submission.status = "submitted"
        submission.submitted_by = request.user
        submission.submitted_at = timezone.now()
        submission.reviewed_by = None
        submission.reviewed_at = None
        submission.review_notes = ""
        submission.published_at = None
        submission.save()

        GradeAuditLog.objects.create(
            submission=submission,
            action="submitted",
            actor=request.user,
            new_data={"status": "submitted"},
        )

        dean_profiles = AcademicStaffProfile.objects.filter(
            institution=profile.institution,
            school=submission.assignment.school,
            academic_role="dean",
            is_active=True,
        ).select_related("user")

        for dean_profile in dean_profiles:
            _notify(
                dean_profile.user,
                (
                    f"{request.user.get_full_name() or request.user.username} submitted "
                    f"{submission.assignment.student}'s {submission.semester} results "
                    "for verification."
                ),
            )

        messages.success(request, "Results submitted to the Dean for verification.")

    return redirect("academics:hod_result_entry", submission_id=submission.pk)


@login_required
def dean_result_queue(request):
    profile = _dean_profile(request.user)
    status = request.GET.get("status", "submitted").strip()
    query = request.GET.get("q", "").strip()
    allowed_statuses = {"submitted", "returned", "published", "all"}

    if status not in allowed_statuses:
        status = "submitted"

    submissions = (
        SemesterResultSubmission.objects.filter(
            assignment__institution=profile.institution,
            assignment__school=profile.school,
        )
        .select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
            "assignment__department",
            "assignment__programme",
            "semester",
            "semester__academic_year",
            "submitted_by",
            "reviewed_by",
        )
        .order_by("-submitted_at", "assignment__student__full_name")
    )

    if status != "all":
        submissions = submissions.filter(status=status)

    if query:
        submissions = submissions.filter(
            Q(assignment__student__full_name__icontains=query)
            | Q(assignment__admission_number__icontains=query)
            | Q(assignment__department__name__icontains=query)
            | Q(assignment__programme__name__icontains=query)
        )

    counts = {
        key: SemesterResultSubmission.objects.filter(
            assignment__institution=profile.institution,
            assignment__school=profile.school,
            status=key,
        ).count()
        for key in ("submitted", "returned", "published")
    }

    return render(
        request,
        "academics/results/dean_queue.html",
        {
            "profile": profile,
            "submissions": submissions,
            "selected_status": status,
            "query": query,
            "counts": counts,
        },
    )


@login_required
def dean_review_results(request, submission_id):
    profile, submission = _dean_submission_or_404(request.user, submission_id)
    grades = list(
        submission.grades.select_related(
            "registration",
            "registration__unit",
        ).order_by("registration__unit__code")
    )
    semester_gpa = _gpa(grades)

    if request.method == "POST":
        form = DeanResultReviewForm(request.POST)

        if submission.status != "submitted":
            messages.error(request, "Only submitted results can be reviewed.")
            return redirect("academics:dean_review_results", submission_id=submission.pk)

        if form.is_valid():
            action = form.cleaned_data["action"]
            notes = form.cleaned_data["review_notes"].strip()
            now = timezone.now()

            with transaction.atomic():
                submission.reviewed_by = request.user
                submission.reviewed_at = now
                submission.review_notes = notes

                if action == "publish":
                    registration_count = StudentUnitRegistration.objects.filter(
                        assignment=submission.assignment,
                        semester=submission.semester,
                        is_active=True,
                    ).count()

                    if not grades or len(grades) != registration_count:
                        messages.error(
                            request,
                            "Results cannot be published because one or more units have no grade.",
                        )
                        return redirect(
                            "academics:dean_review_results",
                            submission_id=submission.pk,
                        )

                    submission.status = "published"
                    submission.published_at = now
                    audit_action = "published"
                    student_message = (
                        f"Your {submission.semester} results have been approved and "
                        "are available for download."
                    )
                else:
                    submission.status = "returned"
                    submission.published_at = None
                    audit_action = "returned"
                    student_message = None

                submission.save()
                GradeAuditLog.objects.create(
                    submission=submission,
                    action=audit_action,
                    actor=request.user,
                    new_data={"status": submission.status},
                    reason=notes,
                )

            if action == "publish":
                _notify(submission.assignment.student.user, student_message)
                messages.success(request, "Results approved and published to the student.")
            else:
                _notify(
                    submission.submitted_by,
                    (
                        f"{submission.assignment.student}'s {submission.semester} "
                        f"results were returned for correction: {notes}"
                    ),
                )
                messages.success(request, "Results returned to the HOD for correction.")

            return redirect("academics:dean_result_queue")
    else:
        form = DeanResultReviewForm()

    return render(
        request,
        "academics/results/dean_review.html",
        {
            "profile": profile,
            "submission": submission,
            "grades": grades,
            "semester_gpa": semester_gpa,
            "form": form,
        },
    )


@login_required
def request_grade_amendment(request, grade_id):
    profile = _hod_profile(request.user)
    grade = get_object_or_404(
        StudentGrade.objects.select_related(
            "submission",
            "submission__assignment",
            "submission__assignment__student",
            "submission__semester",
            "submission__grading_scale",
            "registration",
            "registration__unit",
        ),
        pk=grade_id,
        submission__assignment__department=profile.department,
        submission__assignment__institution=profile.institution,
        submission__status="published",
    )

    if grade.amendment_requests.filter(status="pending").exists():
        messages.info(request, "A pending amendment already exists for this grade.")
        return redirect(
            "academics:hod_result_entry",
            submission_id=grade.submission_id,
        )

    if request.method == "POST":
        form = GradeAmendmentRequestForm(request.POST, grade=grade)

        if form.is_valid():
            amendment = form.save(commit=False)
            amendment.requested_by = request.user
            amendment.save()

            dean_profiles = AcademicStaffProfile.objects.filter(
                institution=profile.institution,
                school=grade.submission.assignment.school,
                academic_role="dean",
                is_active=True,
            ).select_related("user")

            for dean_profile in dean_profiles:
                _notify(
                    dean_profile.user,
                    (
                        f"A grade amendment was requested for "
                        f"{grade.submission.assignment.student}, "
                        f"unit {grade.registration.unit.code}."
                    ),
                )

            messages.success(request, "Grade amendment submitted to the Dean.")
            return redirect(
                "academics:hod_result_entry",
                submission_id=grade.submission_id,
            )
    else:
        form = GradeAmendmentRequestForm(grade=grade)

    return render(
        request,
        "academics/results/request_amendment.html",
        {"profile": profile, "grade": grade, "form": form},
    )


@login_required
def dean_amendment_queue(request):
    profile = _dean_profile(request.user)
    amendments = (
        GradeAmendmentRequest.objects.filter(
            grade__submission__assignment__institution=profile.institution,
            grade__submission__assignment__school=profile.school,
            status="pending",
        )
        .select_related(
            "grade",
            "grade__submission",
            "grade__submission__assignment",
            "grade__submission__assignment__student",
            "grade__registration",
            "grade__registration__unit",
            "requested_by",
        )
        .order_by("-requested_at")
    )

    return render(
        request,
        "academics/results/dean_amendments.html",
        {"profile": profile, "amendments": amendments},
    )


@login_required
def dean_review_amendment(request, amendment_id):
    profile = _dean_profile(request.user)
    amendment = get_object_or_404(
        GradeAmendmentRequest.objects.select_related(
            "grade",
            "grade__submission",
            "grade__submission__assignment",
            "grade__submission__assignment__student",
            "grade__submission__assignment__student__user",
            "grade__registration",
            "grade__registration__unit",
            "requested_by",
        ),
        pk=amendment_id,
        status="pending",
        grade__submission__assignment__institution=profile.institution,
        grade__submission__assignment__school=profile.school,
    )

    if request.method == "POST":
        form = GradeAmendmentReviewForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data["action"]
            notes = form.cleaned_data["review_notes"].strip()
            now = timezone.now()

            with transaction.atomic():
                amendment.reviewed_by = request.user
                amendment.reviewed_at = now
                amendment.review_notes = notes

                if action == "approve":
                    grade = amendment.grade
                    old_data = _grade_snapshot(grade)
                    grade.coursework_mark = amendment.proposed_coursework_mark
                    grade.examination_mark = amendment.proposed_examination_mark
                    grade.entered_by = amendment.requested_by
                    grade.save()
                    amendment.status = "approved"
                    amendment.applied_at = now
                    amendment.save()
                    GradeAuditLog.objects.create(
                        grade=grade,
                        submission=grade.submission,
                        action="amended",
                        actor=request.user,
                        old_data=old_data,
                        new_data=_grade_snapshot(grade),
                        reason=amendment.reason,
                    )
                    message = "The grade amendment was approved and applied."
                else:
                    amendment.status = "rejected"
                    amendment.save()
                    message = "The grade amendment was rejected."

            _notify(amendment.requested_by, message)
            _notify(amendment.grade.submission.assignment.student.user, message)
            messages.success(request, message)
            return redirect("academics:dean_amendment_queue")
    else:
        form = GradeAmendmentReviewForm()

    return render(
        request,
        "academics/results/dean_review_amendment.html",
        {"profile": profile, "amendment": amendment, "form": form},
    )


def _student_assignment(user):
    if getattr(user, "role", "") != "student":
        raise PermissionDenied("Academic results are available only to students.")

    return get_object_or_404(
        StudentAcademicAssignment.objects.select_related(
            "student",
            "student__user",
            "institution",
            "school",
            "department",
            "programme",
        ),
        student__user=user,
        is_active=True,
    )


@login_required
def my_academic_results(request):
    assignment = _student_assignment(request.user)
    submissions = list(
        SemesterResultSubmission.objects.filter(
            assignment=assignment,
            status="published",
        )
        .select_related("semester", "semester__academic_year", "reviewed_by")
        .prefetch_related("grades", "grades__registration__unit")
    )

    for submission in submissions:
        submission.display_gpa = _gpa(list(submission.grades.all()))

    all_grades = [
        grade
        for submission in submissions
        for grade in submission.grades.all()
    ]

    return render(
        request,
        "academics/results/student_results.html",
        {
            "assignment": assignment,
            "submissions": submissions,
            "cumulative_gpa": _gpa(all_grades),
        },
    )


def _document_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocumentTitle",
            parent=styles["Heading1"],
            alignment=TA_CENTER,
            fontSize=15,
            leading=18,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocumentCenter",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=9,
            leading=12,
        )
    )
    return styles


def _institution_header(story, institution, styles):
    if institution.logo:
        try:
            story.append(Image(institution.logo.path, width=20 * mm, height=20 * mm))
        except (FileNotFoundError, OSError, ValueError):
            pass

    story.append(
        Paragraph(
            institution.institution_name.upper(),
            styles["DocumentTitle"],
        )
    )
    contact_parts = [
        value
        for value in (
            institution.address,
            institution.town,
            institution.county,
            institution.official_email,
            institution.phone_number,
        )
        if value
    ]
    story.append(Paragraph(" | ".join(contact_parts), styles["DocumentCenter"]))
    story.append(Spacer(1, 5 * mm))


def _result_table(grades):
    rows = [
        [
            "Unit Code",
            "Unit Title",
            "Credits",
            "CAT",
            "Exam",
            "Total",
            "Grade",
            "Points",
        ]
    ]

    for grade in grades:
        unit = grade.registration.unit
        rows.append(
            [
                unit.code,
                unit.title,
                str(unit.credit_hours),
                str(grade.coursework_mark),
                str(grade.examination_mark),
                str(grade.total_mark),
                grade.letter_grade,
                str(grade.grade_point),
            ]
        )

    table = Table(
        rows,
        repeatRows=1,
        colWidths=[22 * mm, 56 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm, 16 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173f43")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4c8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f7")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


@login_required
def download_result_slip(request, submission_id):
    assignment = _student_assignment(request.user)
    submission = get_object_or_404(
        SemesterResultSubmission.objects.select_related(
            "semester",
            "semester__academic_year",
            "assignment__institution",
            "assignment__school",
            "assignment__department",
            "assignment__programme",
        ),
        pk=submission_id,
        assignment=assignment,
        status="published",
    )
    grades = list(
        submission.grades.select_related(
            "registration",
            "registration__unit",
        ).order_by("registration__unit__code")
    )

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Result Slip - {assignment.admission_number}",
    )
    styles = _document_styles()
    story = []
    _institution_header(story, assignment.institution, styles)
    story.append(Paragraph("OFFICIAL SEMESTER RESULT SLIP", styles["DocumentTitle"]))
    details = [
        ["Student", str(assignment.student), "Admission No.", assignment.admission_number],
        ["Programme", str(assignment.programme or "Not assigned"), "Department", assignment.department.name],
        ["Academic Year", submission.semester.academic_year.name, "Semester", submission.semester.name],
    ]
    detail_table = Table(details, colWidths=[28 * mm, 80 * mm, 30 * mm, 80 * mm])
    detail_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f6f6")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#ccd5d7")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.extend([detail_table, Spacer(1, 5 * mm), _result_table(grades)])
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            f"Semester GPA: <b>{_gpa(grades) if _gpa(grades) is not None else 'N/A'}</b> "
            f"&nbsp;&nbsp; Document No: RS-{submission.pk:08d}",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "This result slip was generated from approved and published academic records.",
            styles["DocumentCenter"],
        )
    )
    document.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="result-slip-{assignment.admission_number or assignment.pk}.pdf"'
    )
    return response


@login_required
def download_transcript(request):
    assignment = _student_assignment(request.user)
    submissions = list(
        SemesterResultSubmission.objects.filter(
            assignment=assignment,
            status="published",
        )
        .select_related("semester", "semester__academic_year")
        .prefetch_related("grades", "grades__registration__unit")
        .order_by("semester__academic_year__starts_on", "semester__number")
    )

    if not submissions:
        messages.error(request, "No published results are available for a transcript.")
        return redirect("academics:my_academic_results")

    all_grades = []
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Academic Transcript - {assignment.admission_number}",
    )
    styles = _document_styles()
    story = []
    _institution_header(story, assignment.institution, styles)
    story.append(Paragraph("PROVISIONAL ACADEMIC TRANSCRIPT", styles["DocumentTitle"]))
    story.append(
        Paragraph(
            (
                f"<b>Student:</b> {assignment.student} &nbsp;&nbsp; "
                f"<b>Admission No:</b> {assignment.admission_number} &nbsp;&nbsp; "
                f"<b>Programme:</b> {assignment.programme or 'Not assigned'}"
            ),
            styles["DocumentCenter"],
        )
    )
    story.append(Spacer(1, 5 * mm))

    for submission in submissions:
        grades = list(submission.grades.all())
        all_grades.extend(grades)
        story.append(
            Paragraph(
                f"{submission.semester.academic_year.name} — {submission.semester.name}",
                styles["Heading3"],
            )
        )
        story.append(_result_table(grades))
        story.append(
            Paragraph(
                f"Semester GPA: <b>{_gpa(grades) if _gpa(grades) is not None else 'N/A'}</b>",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            f"Cumulative GPA: <b>{_gpa(all_grades) if _gpa(all_grades) is not None else 'N/A'}</b> "
            f"&nbsp;&nbsp; Document No: TR-{assignment.pk:08d}",
            styles["Heading3"],
        )
    )
    story.append(
        Paragraph(
            "Provisional transcript generated from Dean-approved academic records.",
            styles["DocumentCenter"],
        )
    )
    document.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="transcript-{assignment.admission_number or assignment.pk}.pdf"'
    )
    return response
