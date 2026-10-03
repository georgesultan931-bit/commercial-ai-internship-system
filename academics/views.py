from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from internships.models import Application, InternshipOpportunity

from .models import (
    AcademicYear,
    AcademicStaffProfile,
    Programme,
    Semester,
    StudentAcademicAssignment,
    SupervisorAcademicAssignment,
    Unit,
)


def assignment_pending(request):
    return render(
        request,
        "academics/assignment_pending.html",
        {
            "academic_role": request.user.get_role_display(),
        },
    )


def academic_period_context(institution):
    """Resolve the institution's current academic year and semester."""

    today = timezone.localdate()

    academic_years = AcademicYear.objects.filter(
        institution=institution,
    )

    current_academic_year = (
        academic_years
        .filter(is_current=True)
        .order_by("-starts_on")
        .first()
    )

    if current_academic_year is None:
        current_academic_year = (
            academic_years
            .filter(
                starts_on__lte=today,
                ends_on__gte=today,
            )
            .order_by("-starts_on")
            .first()
        )

    current_semester = None
    semester_count = 0

    if current_academic_year is not None:
        semesters = Semester.objects.filter(
            academic_year=current_academic_year,
        )

        semester_count = semesters.count()

        current_semester = (
            semesters
            .filter(is_current=True)
            .order_by("number")
            .first()
        )

        if current_semester is None:
            current_semester = (
                semesters
                .filter(
                    starts_on__lte=today,
                    ends_on__gte=today,
                )
                .order_by("number")
                .first()
            )

    return {
        "current_academic_year": current_academic_year,
        "current_semester": current_semester,
        "semester_count": semester_count,
    }


@login_required
def dashboard(request):
    role = getattr(request.user, "role", "")

    if role not in {"hod", "dean"}:
        messages.error(
            request,
            "This dashboard is available only to HOD and Dean accounts.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
            "department",
        )
        .filter(
            user=request.user,
            is_active=True,
        )
        .first()
    )

    if profile is None or profile.academic_role != role:
        return assignment_pending(request)

    if role == "hod":
        if not profile.department_id:
            return assignment_pending(request)

        department = profile.department

        programmes = department.programmes.filter(
            is_active=True,
        )

        units = Unit.objects.filter(
            programme__department=department,
            is_active=True,
        ).select_related("programme")

        academic_period = academic_period_context(
            profile.institution,
        )

        current_semester = academic_period[
            "current_semester"
        ]

        semester_unit_count = 0

        if current_semester is not None:
            semester_unit_count = units.filter(
                semester_number=current_semester.number,
            ).count()

        unit_groups = (
            units
            .values(
                "year_of_study",
                "semester_number",
            )
            .annotate(total=Count("id"))
            .order_by(
                "year_of_study",
                "semester_number",
            )
        )

        student_assignments = (
            StudentAcademicAssignment.objects
            .filter(
                department=department,
                is_active=True,
            )
            .select_related(
                "student",
                "student__user",
                "programme",
            )
        )

        supervisor_assignments = (
            SupervisorAcademicAssignment.objects
            .filter(
                department=department,
                is_active=True,
            )
            .select_related(
                "supervisor",
                "supervisor__user",
            )
        )

        applications = (
            Application.objects
            .filter(
                student__academic_assignment__department=department,
                student__academic_assignment__is_active=True,
            )
            .select_related(
                "student",
                "student__user",
                "opportunity",
                "opportunity__employer",
            )
            .order_by("-applied_at")
        )

        opportunity_ids = applications.values_list(
            "opportunity_id",
            flat=True,
        )

        active_internships_count = (
            InternshipOpportunity.objects
            .filter(
                id__in=opportunity_ids,
                status="open",
            )
            .distinct()
            .count()
        )

        return render(
            request,
            "academics/hod_dashboard.html",
            {
                "profile": profile,
                "department": department,
                "programmes": programmes,
                "programme_count": programmes.count(),
                "unit_count": units.count(),
                "semester_unit_count": semester_unit_count,
                "unit_groups": unit_groups,
                "recent_units": units.order_by(
                    "year_of_study",
                    "semester_number",
                    "code",
                )[:8],
                "students_count": student_assignments.count(),
                "supervisors_count": supervisor_assignments.count(),
                "internships_count": active_internships_count,
                "pending_applications_count": applications.filter(
                    status="pending",
                ).count(),
                "recent_applications": applications[:5],
                **academic_period,
            },
        )

    if not profile.school_id:
        return assignment_pending(request)

    school = profile.school

    departments = (
        school.departments
        .filter(is_active=True)
        .annotate(
            programme_total=Count(
                "programmes",
                filter=Q(
                    programmes__is_active=True,
                ),
                distinct=True,
            ),
            unit_total=Count(
                "programmes__units",
                filter=Q(
                    programmes__units__is_active=True,
                ),
                distinct=True,
            ),
            student_total=Count(
                "student_academic_assignments",
                filter=Q(
                    student_academic_assignments__is_active=True,
                ),
                distinct=True,
            ),
        )
    )

    programmes = Programme.objects.filter(
        department__school=school,
        is_active=True,
    )

    units = (
        Unit.objects
        .filter(
            programme__department__school=school,
            is_active=True,
        )
        .select_related(
            "programme",
            "programme__department",
        )
    )

    academic_period = academic_period_context(
        profile.institution,
    )

    current_semester = academic_period[
        "current_semester"
    ]

    semester_unit_count = 0

    if current_semester is not None:
        semester_unit_count = units.filter(
            semester_number=current_semester.number,
        ).count()

    student_assignments = (
        StudentAcademicAssignment.objects
        .filter(
            school=school,
            is_active=True,
        )
        .select_related(
            "student",
            "student__user",
            "department",
            "programme",
        )
    )

    supervisor_assignments = (
        SupervisorAcademicAssignment.objects
        .filter(
            school=school,
            is_active=True,
        )
        .select_related(
            "supervisor",
            "supervisor__user",
            "department",
        )
    )

    applications = (
        Application.objects
        .filter(
            student__academic_assignment__school=school,
            student__academic_assignment__is_active=True,
        )
        .select_related(
            "student",
            "student__user",
            "opportunity",
            "opportunity__employer",
        )
        .order_by("-applied_at")
    )

    opportunity_ids = applications.values_list(
        "opportunity_id",
        flat=True,
    )

    active_internships_count = (
        InternshipOpportunity.objects
        .filter(
            id__in=opportunity_ids,
            status="open",
        )
        .distinct()
        .count()
    )

    return render(
        request,
        "academics/dean_dashboard.html",
        {
            "profile": profile,
            "school": school,
            "departments": departments,
            "department_count": departments.count(),
            "programme_count": programmes.count(),
            "unit_count": units.count(),
            "semester_unit_count": semester_unit_count,
            "students_count": student_assignments.count(),
            "supervisors_count": supervisor_assignments.count(),
            "internships_count": active_internships_count,
            "pending_applications_count": applications.filter(
                status="pending",
            ).count(),
            "recent_applications": applications[:5],
            **academic_period,
        },
    )


@login_required
def department_students(request):
    if getattr(request.user, "role", "") != "hod":
        messages.error(
            request,
            "Only a Head of Department can access student oversight.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
            "department",
        )
        .filter(
            user=request.user,
            academic_role="hod",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.department_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()

    assignments = (
        StudentAcademicAssignment.objects
        .filter(
            department=profile.department,
            is_active=True,
        )
        .select_related(
            "student",
            "student__user",
            "institution",
            "school",
            "department",
            "programme",
        )
        .order_by(
            "student__full_name",
            "student__user__username",
        )
    )

    if search:
        assignments = assignments.filter(
            Q(student__full_name__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(student__surname__icontains=search)
            | Q(student__user__username__icontains=search)
            | Q(student__user__email__icontains=search)
            | Q(admission_number__icontains=search)
            | Q(programme__name__icontains=search)
            | Q(programme__code__icontains=search)
        )

    paginator = Paginator(assignments, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    student_ids = [
        assignment.student_id
        for assignment in page_obj.object_list
    ]

    application_rows = (
        Application.objects
        .filter(student_id__in=student_ids)
        .values("student_id")
        .annotate(
            total=Count("id"),
            pending=Count(
                "id",
                filter=Q(status="pending"),
            ),
            accepted=Count(
                "id",
                filter=Q(status="accepted"),
            ),
        )
    )

    application_summary = {
        row["student_id"]: row
        for row in application_rows
    }

    for assignment in page_obj.object_list:
        summary = application_summary.get(
            assignment.student_id,
            {},
        )

        assignment.total_applications = summary.get("total", 0)
        assignment.pending_applications = summary.get("pending", 0)
        assignment.accepted_applications = summary.get("accepted", 0)

    return render(
        request,
        "academics/department_students.html",
        {
            "profile": profile,
            "department": profile.department,
            "page_obj": page_obj,
            "search": search,
            "total_students": assignments.count(),
        },
    )

@login_required
def department_supervisors(request):
    if getattr(request.user, "role", "") != "hod":
        messages.error(
            request,
            "Only a Head of Department can access supervisor management.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
            "department",
        )
        .filter(
            user=request.user,
            academic_role="hod",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.department_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()

    assignments = (
        SupervisorAcademicAssignment.objects
        .filter(
            department=profile.department,
            is_active=True,
        )
        .select_related(
            "supervisor",
            "supervisor__user",
            "institution",
            "school",
            "department",
        )
        .order_by(
            "supervisor__full_name",
            "supervisor__user__username",
        )
    )

    if search:
        assignments = assignments.filter(
            Q(supervisor__full_name__icontains=search)
            | Q(supervisor__staff_number__icontains=search)
            | Q(supervisor__job_title__icontains=search)
            | Q(supervisor__specialization__icontains=search)
            | Q(supervisor__official_email__icontains=search)
            | Q(supervisor__user__email__icontains=search)
            | Q(supervisor__user__username__icontains=search)
        )

    total_supervisors = assignments.count()

    paginator = Paginator(assignments, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "academics/department_supervisors.html",
        {
            "profile": profile,
            "department": profile.department,
            "page_obj": page_obj,
            "search": search,
            "total_supervisors": total_supervisors,
        },
    )


@login_required
def department_applications(request):
    if getattr(request.user, "role", "") != "hod":
        messages.error(
            request,
            "Only a Head of Department can access application monitoring.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
            "department",
        )
        .filter(
            user=request.user,
            academic_role="hod",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.department_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()

    valid_statuses = {
        value
        for value, label in Application.STATUS_CHOICES
    }

    if status_filter not in valid_statuses:
        status_filter = ""

    applications = (
        Application.objects
        .filter(
            student__academic_assignment__department=profile.department,
            student__academic_assignment__is_active=True,
        )
        .select_related(
            "student",
            "student__user",
            "opportunity",
            "opportunity__employer",
        )
        .order_by("-applied_at")
    )

    if search:
        applications = applications.filter(
            Q(student__full_name__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(student__surname__icontains=search)
            | Q(student__user__username__icontains=search)
            | Q(student__user__email__icontains=search)
            | Q(opportunity__title__icontains=search)
            | Q(opportunity__employer__company_name__icontains=search)
            | Q(opportunity__location__icontains=search)
        )

    status_rows = (
        applications
        .values("status")
        .annotate(total=Count("id"))
    )

    status_counts = {
        row["status"]: row["total"]
        for row in status_rows
    }

    if status_filter:
        applications = applications.filter(status=status_filter)

    total_applications = applications.count()
    paginator = Paginator(applications, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "academics/department_applications.html",
        {
            "profile": profile,
            "department": profile.department,
            "page_obj": page_obj,
            "search": search,
            "status_filter": status_filter,
            "status_choices": Application.STATUS_CHOICES,
            "status_counts": status_counts,
            "total_applications": total_applications,
        },
    )

@login_required
def department_internships(request):
    if getattr(request.user, "role", "") != "hod":
        messages.error(
            request,
            "Only a Head of Department can access internship tracking.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
            "department",
        )
        .filter(
            user=request.user,
            academic_role="hod",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.department_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()

    placements = (
        Application.objects
        .filter(
            student__academic_assignment__department=profile.department,
            student__academic_assignment__is_active=True,
            status="accepted",
        )
        .select_related(
            "student",
            "student__user",
            "opportunity",
            "opportunity__employer",
        )
        .order_by(
            "student__full_name",
            "-applied_at",
        )
    )

    if search:
        placements = placements.filter(
            Q(student__full_name__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(student__surname__icontains=search)
            | Q(student__user__username__icontains=search)
            | Q(student__user__email__icontains=search)
            | Q(opportunity__title__icontains=search)
            | Q(opportunity__employer__company_name__icontains=search)
            | Q(opportunity__location__icontains=search)
        )

    total_internships = placements.count()
    paginator = Paginator(placements, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "academics/department_internships.html",
        {
            "profile": profile,
            "department": profile.department,
            "page_obj": page_obj,
            "search": search,
            "total_internships": total_internships,
        },
    )

@login_required
def school_departments(request):
    if getattr(request.user, "role", "") != "dean":
        messages.error(
            request,
            "Only a Dean can access school department oversight.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
        )
        .filter(
            user=request.user,
            academic_role="dean",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.school_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()

    departments = profile.school.departments.all().order_by("name")

    if search:
        departments = departments.filter(
            Q(name__icontains=search)
            | Q(code__icontains=search)
        )

    department_list = list(departments)

    department_ids = [
        department.id
        for department in department_list
    ]

    programme_rows = (
        Programme.objects
        .filter(
            department_id__in=department_ids,
            is_active=True,
        )
        .values("department_id")
        .annotate(total=Count("id"))
    )

    student_rows = (
        StudentAcademicAssignment.objects
        .filter(
            department_id__in=department_ids,
            is_active=True,
        )
        .values("department_id")
        .annotate(total=Count("id"))
    )

    supervisor_rows = (
        SupervisorAcademicAssignment.objects
        .filter(
            department_id__in=department_ids,
            is_active=True,
        )
        .values("department_id")
        .annotate(total=Count("id"))
    )

    hod_profiles = (
        AcademicStaffProfile.objects
        .filter(
            department_id__in=department_ids,
            academic_role="hod",
            is_active=True,
        )
        .select_related("user")
    )

    programme_counts = {
        row["department_id"]: row["total"]
        for row in programme_rows
    }

    student_counts = {
        row["department_id"]: row["total"]
        for row in student_rows
    }

    supervisor_counts = {
        row["department_id"]: row["total"]
        for row in supervisor_rows
    }

    hod_by_department = {
        hod.department_id: hod
        for hod in hod_profiles
    }

    for department in department_list:
        department.programme_total = programme_counts.get(
            department.id,
            0,
        )

        department.student_total = student_counts.get(
            department.id,
            0,
        )

        department.supervisor_total = supervisor_counts.get(
            department.id,
            0,
        )

        department.hod_profile = hod_by_department.get(
            department.id,
        )

    paginator = Paginator(department_list, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "academics/school_departments.html",
        {
            "profile": profile,
            "school": profile.school,
            "page_obj": page_obj,
            "search": search,
            "total_departments": len(department_list),
        },
    )

@login_required
def school_students(request):
    if getattr(request.user, "role", "") != "dean":
        messages.error(
            request,
            "Only a Dean can access school student oversight.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
        )
        .filter(
            user=request.user,
            academic_role="dean",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.school_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()
    department_filter = request.GET.get("department", "").strip()

    departments = profile.school.departments.filter(
        is_active=True,
    ).order_by("name")

    valid_department_ids = {
        str(department_id)
        for department_id in departments.values_list("id", flat=True)
    }

    if department_filter not in valid_department_ids:
        department_filter = ""

    assignments = (
        StudentAcademicAssignment.objects
        .filter(
            school=profile.school,
            is_active=True,
        )
        .select_related(
            "student",
            "student__user",
            "institution",
            "school",
            "department",
            "programme",
        )
        .order_by(
            "department__name",
            "student__full_name",
            "student__user__username",
        )
    )

    if department_filter:
        assignments = assignments.filter(
            department_id=department_filter,
        )

    if search:
        assignments = assignments.filter(
            Q(student__full_name__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(student__surname__icontains=search)
            | Q(student__user__username__icontains=search)
            | Q(student__user__email__icontains=search)
            | Q(admission_number__icontains=search)
            | Q(programme__name__icontains=search)
            | Q(programme__code__icontains=search)
            | Q(department__name__icontains=search)
        )

    total_students = assignments.count()
    paginator = Paginator(assignments, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    student_ids = [
        assignment.student_id
        for assignment in page_obj.object_list
    ]

    application_rows = (
        Application.objects
        .filter(student_id__in=student_ids)
        .values("student_id")
        .annotate(
            total=Count("id"),
            pending=Count(
                "id",
                filter=Q(status="pending"),
            ),
            accepted=Count(
                "id",
                filter=Q(status="accepted"),
            ),
        )
    )

    application_summary = {
        row["student_id"]: row
        for row in application_rows
    }

    for assignment in page_obj.object_list:
        summary = application_summary.get(
            assignment.student_id,
            {},
        )

        assignment.total_applications = summary.get("total", 0)
        assignment.pending_applications = summary.get("pending", 0)
        assignment.accepted_applications = summary.get("accepted", 0)

    return render(
        request,
        "academics/school_students.html",
        {
            "profile": profile,
            "school": profile.school,
            "departments": departments,
            "page_obj": page_obj,
            "search": search,
            "department_filter": department_filter,
            "total_students": total_students,
        },
    )

@login_required
def school_supervisors(request):
    if getattr(request.user, "role", "") != "dean":
        messages.error(
            request,
            "Only a Dean can access school supervisor oversight.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
        )
        .filter(
            user=request.user,
            academic_role="dean",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.school_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()
    department_filter = request.GET.get("department", "").strip()

    departments = profile.school.departments.filter(
        is_active=True,
    ).order_by("name")

    valid_department_ids = {
        str(department_id)
        for department_id in departments.values_list("id", flat=True)
    }

    if department_filter not in valid_department_ids:
        department_filter = ""

    assignments = (
        SupervisorAcademicAssignment.objects
        .filter(
            school=profile.school,
            is_active=True,
        )
        .select_related(
            "supervisor",
            "supervisor__user",
            "institution",
            "school",
            "department",
        )
        .order_by(
            "department__name",
            "supervisor__full_name",
            "supervisor__user__username",
        )
    )

    if department_filter:
        assignments = assignments.filter(
            department_id=department_filter,
        )

    if search:
        assignments = assignments.filter(
            Q(supervisor__full_name__icontains=search)
            | Q(supervisor__staff_number__icontains=search)
            | Q(supervisor__job_title__icontains=search)
            | Q(supervisor__specialization__icontains=search)
            | Q(supervisor__official_email__icontains=search)
            | Q(supervisor__user__email__icontains=search)
            | Q(supervisor__user__username__icontains=search)
            | Q(department__name__icontains=search)
        )

    total_supervisors = assignments.count()
    paginator = Paginator(assignments, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "academics/school_supervisors.html",
        {
            "profile": profile,
            "school": profile.school,
            "departments": departments,
            "page_obj": page_obj,
            "search": search,
            "department_filter": department_filter,
            "total_supervisors": total_supervisors,
        },
    )

@login_required
def school_internships(request):
    if getattr(request.user, "role", "") != "dean":
        messages.error(
            request,
            "Only a Dean can access school internship tracking.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
        )
        .filter(
            user=request.user,
            academic_role="dean",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.school_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()
    department_filter = request.GET.get("department", "").strip()

    departments = profile.school.departments.filter(
        is_active=True,
    ).order_by("name")

    valid_department_ids = {
        str(department_id)
        for department_id in departments.values_list("id", flat=True)
    }

    if department_filter not in valid_department_ids:
        department_filter = ""

    placements = (
        Application.objects
        .filter(
            student__academic_assignment__school=profile.school,
            student__academic_assignment__is_active=True,
            status="accepted",
        )
        .select_related(
            "student",
            "student__user",
            "student__academic_assignment",
            "student__academic_assignment__department",
            "student__academic_assignment__programme",
            "opportunity",
            "opportunity__employer",
        )
        .order_by(
            "student__academic_assignment__department__name",
            "student__full_name",
            "-applied_at",
        )
    )

    if department_filter:
        placements = placements.filter(
            student__academic_assignment__department_id=department_filter,
        )

    if search:
        placements = placements.filter(
            Q(student__full_name__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(student__surname__icontains=search)
            | Q(student__user__username__icontains=search)
            | Q(student__user__email__icontains=search)
            | Q(opportunity__title__icontains=search)
            | Q(opportunity__employer__company_name__icontains=search)
            | Q(opportunity__location__icontains=search)
            | Q(
                student__academic_assignment__department__name__icontains=search
            )
        )

    total_internships = placements.count()
    paginator = Paginator(placements, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "academics/school_internships.html",
        {
            "profile": profile,
            "school": profile.school,
            "departments": departments,
            "page_obj": page_obj,
            "search": search,
            "department_filter": department_filter,
            "total_internships": total_internships,
        },
    )

@login_required
def school_applications(request):
    if getattr(request.user, "role", "") != "dean":
        messages.error(
            request,
            "Only a Dean can access school application monitoring.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
        )
        .filter(
            user=request.user,
            academic_role="dean",
            is_active=True,
        )
        .first()
    )

    if profile is None or not profile.school_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()
    department_filter = request.GET.get("department", "").strip()
    status_filter = request.GET.get("status", "").strip()

    departments = profile.school.departments.filter(
        is_active=True,
    ).order_by("name")

    valid_department_ids = {
        str(department_id)
        for department_id in departments.values_list("id", flat=True)
    }

    if department_filter not in valid_department_ids:
        department_filter = ""

    valid_statuses = {
        value
        for value, label in Application.STATUS_CHOICES
    }

    if status_filter not in valid_statuses:
        status_filter = ""

    applications = (
        Application.objects
        .filter(
            student__academic_assignment__school=profile.school,
            student__academic_assignment__is_active=True,
        )
        .select_related(
            "student",
            "student__user",
            "student__academic_assignment",
            "student__academic_assignment__department",
            "student__academic_assignment__programme",
            "opportunity",
            "opportunity__employer",
        )
        .order_by("-applied_at")
    )

    if department_filter:
        applications = applications.filter(
            student__academic_assignment__department_id=department_filter,
        )

    if search:
        applications = applications.filter(
            Q(student__full_name__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(student__surname__icontains=search)
            | Q(student__user__username__icontains=search)
            | Q(student__user__email__icontains=search)
            | Q(opportunity__title__icontains=search)
            | Q(opportunity__employer__company_name__icontains=search)
            | Q(opportunity__location__icontains=search)
            | Q(
                student__academic_assignment__department__name__icontains=search
            )
        )

    if status_filter:
        applications = applications.filter(status=status_filter)

    total_applications = applications.count()
    paginator = Paginator(applications, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "academics/school_applications.html",
        {
            "profile": profile,
            "school": profile.school,
            "departments": departments,
            "page_obj": page_obj,
            "search": search,
            "department_filter": department_filter,
            "status_filter": status_filter,
            "status_choices": Application.STATUS_CHOICES,
            "total_applications": total_applications,
        },
    )



# -----------------------------------------------------------------------------
# Academic Reports and Progress
# Append this block to the END of academics/views.py.
# -----------------------------------------------------------------------------

from django.db.models import Sum

from institutions.models import (
    PlacementAssignment,
    PlacementProgressReport,
    SupervisorEvaluation,
)

from .models import Department


@login_required
def academic_reports(request):
    role = getattr(request.user, "role", "")

    if role not in {"hod", "dean"}:
        messages.error(
            request,
            "Academic reports are available only to HOD and Dean accounts.",
        )
        return redirect("dashboard")

    profile = (
        AcademicStaffProfile.objects
        .select_related(
            "institution",
            "school",
            "department",
        )
        .filter(
            user=request.user,
            academic_role=role,
            is_active=True,
        )
        .first()
    )

    if profile is None:
        return assignment_pending(request)

    if role == "hod" and not profile.department_id:
        return assignment_pending(request)

    if role == "dean" and not profile.school_id:
        return assignment_pending(request)

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    department_filter = request.GET.get("department", "").strip()

    valid_statuses = {
        value
        for value, label in PlacementAssignment.STATUS_CHOICES
    }

    if status_filter not in valid_statuses:
        status_filter = ""

    departments = Department.objects.none()

    if role == "hod":
        scope_name = profile.department.name
        base_placements = PlacementAssignment.objects.filter(
            student__academic_assignment__department=profile.department,
            student__academic_assignment__is_active=True,
        )
        department_filter = ""
    else:
        scope_name = profile.school.name
        departments = profile.school.departments.filter(
            is_active=True,
        ).order_by("name")

        valid_department_ids = {
            str(department_id)
            for department_id in departments.values_list("id", flat=True)
        }

        if department_filter not in valid_department_ids:
            department_filter = ""

        base_placements = PlacementAssignment.objects.filter(
            student__academic_assignment__school=profile.school,
            student__academic_assignment__is_active=True,
        )

    placement_ids = base_placements.values("id")

    progress_reports = PlacementProgressReport.objects.filter(
        assignment_id__in=placement_ids,
    )

    evaluations = SupervisorEvaluation.objects.filter(
        assignment_id__in=placement_ids,
    )

    summary = {
        "total_placements": base_placements.count(),
        "ongoing_placements": base_placements.filter(
            status="ongoing",
        ).count(),
        "completed_placements": base_placements.filter(
            status="completed",
        ).count(),
        "pending_placements": base_placements.filter(
            status__in=("pending", "assigned"),
        ).count(),
        "submitted_reports": progress_reports.filter(
            status="submitted",
        ).count(),
        "reviewed_reports": progress_reports.filter(
            status="reviewed",
        ).count(),
        "revision_reports": progress_reports.filter(
            status="revision_required",
        ).count(),
        "evaluation_count": evaluations.count(),
        "total_hours": (
            progress_reports.aggregate(total=Sum("hours_worked"))["total"]
            or 0
        ),
    }

    placements = (
        base_placements
        .select_related(
            "student",
            "student__user",
            "student__academic_assignment",
            "student__academic_assignment__department",
            "student__academic_assignment__programme",
            "supervisor",
            "supervisor__user",
            "application",
            "application__opportunity",
            "application__opportunity__employer",
        )
        .prefetch_related(
            "progress_reports",
            "evaluations",
        )
        .order_by(
            "student__academic_assignment__department__name",
            "student__full_name",
            "-created_at",
        )
    )

    if role == "dean" and department_filter:
        placements = placements.filter(
            student__academic_assignment__department_id=department_filter,
        )

    if status_filter:
        placements = placements.filter(status=status_filter)

    if search:
        placements = placements.filter(
            Q(student__full_name__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(student__surname__icontains=search)
            | Q(student__user__username__icontains=search)
            | Q(student__user__email__icontains=search)
            | Q(supervisor__full_name__icontains=search)
            | Q(application__opportunity__title__icontains=search)
            | Q(
                student__academic_assignment__department__name__icontains=search
            )
        )

    total_results = placements.count()
    paginator = Paginator(placements, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    for placement in page_obj.object_list:
        placement.report_total = len(placement.progress_reports.all())
        placement.evaluation_total = len(placement.evaluations.all())
        placement.hours_total = sum(
            report.hours_worked
            for report in placement.progress_reports.all()
        )

    return render(
        request,
        "academics/academic_reports.html",
        {
            "profile": profile,
            "role": role,
            "scope_name": scope_name,
            "department": profile.department,
            "school": profile.school,
            "departments": departments,
            "summary": summary,
            "page_obj": page_obj,
            "search": search,
            "status_filter": status_filter,
            "department_filter": department_filter,
            "status_choices": PlacementAssignment.STATUS_CHOICES,
            "total_results": total_results,
        },
    )
