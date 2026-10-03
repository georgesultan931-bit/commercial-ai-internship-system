from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from academics.models import StudentAcademicAssignment
from internships.models import InternshipOpportunity
from notifications.models import Notification
from students.models import StudentProfile

from .forms import (
    PlacementAssistanceRequestForm,
    StudentVerificationForm,
)
from .models import (
    PLACEMENT_ASSISTANCE_FEE,
    PlacementAssistanceRequest,
    StudentVerification,
)


def student_access_check(request):
    if request.user.role == "student":
        return None

    messages.error(
        request,
        (
            "Placement assistance is available only "
            "to student accounts."
        ),
    )

    return redirect("dashboard")


def institution_access_check(request):
    if request.user.role != "institution":
        messages.error(
            request,
            (
                "Student verification reviews are available "
                "only to institution accounts."
            ),
        )

        return None, redirect("dashboard")

    institution = getattr(
        request.user,
        "institution_profile",
        None,
    )

    if institution is None:
        messages.error(
            request,
            (
                "Complete your institution profile before "
                "reviewing student verification requests."
            ),
        )

        return None, redirect("dashboard")

    return institution, None


def get_student_assignment(request):
    student = (
        StudentProfile.objects
        .select_related(
            "user",
            "institution_profile",
        )
        .filter(
            user=request.user,
        )
        .first()
    )

    if student is None:
        return None, None

    assignment = (
        StudentAcademicAssignment.objects
        .select_related(
            "student",
            "student__user",
            "institution",
            "school",
            "department",
            "programme",
        )
        .filter(
            student=student,
            is_active=True,
        )
        .first()
    )

    return student, assignment


@login_required
def placement_assistance_home(request):
    access_response = student_access_check(
        request
    )

    if access_response:
        return access_response

    student, assignment = get_student_assignment(
        request
    )

    verification = None
    placement_request = None
    payment_transactions = []

    if assignment is not None:
        verification = (
            StudentVerification.objects
            .filter(
                assignment=assignment,
            )
            .select_related(
                "verified_by",
            )
            .first()
        )

        placement_request = (
            PlacementAssistanceRequest.objects
            .filter(
                assignment=assignment,
            )
            .first()
        )

        if placement_request is not None:
            payment_transactions = (
                placement_request
                .payment_transactions
                .all()
            )

    verification_form = None

    if (
        assignment is not None
        and (
            verification is None
            or verification.status == "rejected"
        )
    ):
        verification_form = StudentVerificationForm(
            instance=verification,
        )

    verification_is_verified = (
        verification is not None
        and verification.status == "verified"
    )

    return render(
        request,
        "payments/placement_assistance.html",
        {
            "student": student,
            "assignment": assignment,
            "verification": verification,
            "verification_form": verification_form,
            "verification_is_verified": (
                verification_is_verified
            ),
            "placement_request": placement_request,
            "payment_transactions": payment_transactions,
            "placement_fee": (
                PLACEMENT_ASSISTANCE_FEE
            ),
        },
    )


@login_required
def submit_verification(request):
    access_response = student_access_check(
        request
    )

    if access_response:
        return access_response

    if request.method != "POST":
        return redirect(
            "payments:placement_assistance"
        )

    student, assignment = get_student_assignment(
        request
    )

    if student is None:
        messages.error(
            request,
            "Complete your student profile first.",
        )

        return redirect(
            "payments:placement_assistance"
        )

    if assignment is None:
        messages.error(
            request,
            (
                "Your institution has not created an "
                "active academic assignment for you."
            ),
        )

        return redirect(
            "payments:placement_assistance"
        )

    existing_verification = (
        StudentVerification.objects
        .filter(
            assignment=assignment,
        )
        .first()
    )

    if (
        existing_verification is not None
        and existing_verification.status
        in {
            "pending",
            "verified",
        }
    ):
        messages.info(
            request,
            (
                "Your verification request has already "
                "been submitted."
            ),
        )

        return redirect(
            "payments:placement_assistance"
        )

    form = StudentVerificationForm(
        request.POST,
        request.FILES,
        instance=existing_verification,
    )

    if not form.is_valid():
        placement_request = (
            PlacementAssistanceRequest.objects
            .filter(
                assignment=assignment,
            )
            .first()
        )

        return render(
            request,
            "payments/placement_assistance.html",
            {
                "student": student,
                "assignment": assignment,
                "verification": (
                    existing_verification
                ),
                "verification_form": form,
                "verification_is_verified": False,
                "placement_request": placement_request,
                "payment_transactions": [],
                "placement_fee": (
                    PLACEMENT_ASSISTANCE_FEE
                ),
            },
        )

    with transaction.atomic():
        verification = form.save(
            commit=False
        )

        verification.assignment = assignment
        verification.status = "pending"
        verification.verified_by = None
        verification.verified_at = None
        verification.rejection_reason = ""
        verification.institution_notes = ""

        if (
            verification.verification_method
            == "academic_record"
        ):
            verification.student_id_document = None

        verification.save()

        Notification.objects.create(
            user=assignment.institution.user,
            message=(
                "New student verification request from "
                f"{verification.student}. "
                "Review it under Student Verifications."
            ),
        )

    messages.success(
        request,
        (
            "Your verification request was submitted. "
            "Your institution must approve it before "
            "payment can begin."
        ),
    )

    return redirect(
        "payments:placement_assistance"
    )


@login_required
def placement_preferences(request):
    access_response = student_access_check(
        request
    )

    if access_response:
        return access_response

    student, assignment = get_student_assignment(
        request
    )

    if student is None or assignment is None:
        messages.error(
            request,
            (
                "An active academic assignment is "
                "required."
            ),
        )

        return redirect(
            "payments:placement_assistance"
        )

    verification = (
        StudentVerification.objects
        .filter(
            assignment=assignment,
            status="verified",
        )
        .first()
    )

    if verification is None:
        messages.error(
            request,
            (
                "Your institution must verify you "
                "before you submit placement preferences."
            ),
        )

        return redirect(
            "payments:placement_assistance"
        )

    placement_request = (
        PlacementAssistanceRequest.objects
        .filter(
            assignment=assignment,
        )
        .first()
    )

    if (
        placement_request is not None
        and (
            placement_request.is_paid
            or placement_request.status
            in {
                "active",
                "matching",
                "shortlisted",
                "placed",
            }
        )
    ):
        messages.info(
            request,
            (
                "Your placement request has already "
                "been activated and can no longer "
                "be edited."
            ),
        )

        return redirect(
            "payments:placement_assistance"
        )

    if request.method == "POST":
        form = PlacementAssistanceRequestForm(
            request.POST,
            instance=placement_request,
        )

        if form.is_valid():
            with transaction.atomic():
                placement_request = form.save(
                    commit=False
                )

                placement_request.assignment = (
                    assignment
                )

                placement_request.verification = (
                    verification
                )

                placement_request.status = (
                    "awaiting_payment"
                )

                placement_request.save()

            messages.success(
                request,
                (
                    "Your placement preferences were "
                    "saved. Review the KES 1,500 fee "
                    "before initiating payment."
                ),
            )

            return redirect(
                "payments:placement_assistance"
            )
    else:
        form = PlacementAssistanceRequestForm(
            instance=placement_request,
        )

    return render(
        request,
        "payments/placement_preferences.html",
        {
            "form": form,
            "student": student,
            "assignment": assignment,
            "verification": verification,
            "placement_request": placement_request,
            "placement_fee": (
                PLACEMENT_ASSISTANCE_FEE
            ),
        },
    )


@login_required
def institution_verifications(request):
    institution, access_response = (
        institution_access_check(request)
    )

    if access_response:
        return access_response

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    allowed_statuses = {
        "pending",
        "verified",
        "rejected",
    }

    verifications = (
        StudentVerification.objects
        .select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
            "assignment__institution",
            "assignment__school",
            "assignment__department",
            "assignment__programme",
            "verified_by",
        )
        .filter(
            assignment__institution=institution,
        )
        .order_by(
            "-submitted_at",
        )
    )

    if status_filter in allowed_statuses:
        verifications = verifications.filter(
            status=status_filter,
        )
    else:
        status_filter = ""

    if search:
        verifications = verifications.filter(
            Q(
                assignment__student__full_name__icontains=search
            )
            | Q(
                assignment__student__user__username__icontains=search
            )
            | Q(
                assignment__student__user__email__icontains=search
            )
            | Q(
                assignment__admission_number__icontains=search
            )
            | Q(
                assignment__programme__name__icontains=search
            )
        )

    all_institution_verifications = (
        StudentVerification.objects
        .filter(
            assignment__institution=institution,
        )
    )

    status_counts = {
        "all": (
            all_institution_verifications.count()
        ),
        "pending": (
            all_institution_verifications
            .filter(
                status="pending",
            )
            .count()
        ),
        "verified": (
            all_institution_verifications
            .filter(
                status="verified",
            )
            .count()
        ),
        "rejected": (
            all_institution_verifications
            .filter(
                status="rejected",
            )
            .count()
        ),
    }

    paginator = Paginator(
        verifications,
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "payments/institution_verifications.html",
        {
            "institution": institution,
            "page_obj": page_obj,
            "search": search,
            "status_filter": status_filter,
            "status_counts": status_counts,
            "status_choices": (
                StudentVerification.STATUS_CHOICES
            ),
        },
    )


@login_required
def review_verification(
    request,
    verification_id,
):
    institution, access_response = (
        institution_access_check(request)
    )

    if access_response:
        return access_response

    if request.method != "POST":
        messages.error(
            request,
            "Verification decisions must be submitted securely.",
        )

        return redirect(
            "payments:institution_verifications"
        )

    verification = get_object_or_404(
        StudentVerification.objects
        .select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
            "assignment__institution",
        ),
        id=verification_id,
        assignment__institution=institution,
    )

    action = request.POST.get(
        "action",
        "",
    ).strip().lower()

    institution_notes = request.POST.get(
        "institution_notes",
        "",
    ).strip()

    rejection_reason = request.POST.get(
        "rejection_reason",
        "",
    ).strip()

    if action not in {
        "approve",
        "reject",
    }:
        messages.error(
            request,
            "Select either Approve or Reject.",
        )

        return redirect(
            "payments:institution_verifications"
        )

    if action == "approve" and not institution.is_verified:
        messages.error(
            request,
            (
                "Your institution must be verified before "
                "approving student identity requests."
            ),
        )

        return redirect(
            "payments:institution_verifications"
        )

    if action == "reject" and not rejection_reason:
        messages.error(
            request,
            (
                "A rejection reason is required so the "
                "student knows what to correct."
            ),
        )

        return redirect(
            "payments:institution_verifications"
        )

    with transaction.atomic():
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.institution_notes = (
            institution_notes
        )

        if action == "approve":
            verification.status = "verified"
            verification.rejection_reason = ""

            student_message = (
                "Your student verification was approved by "
                f"{institution.institution_name}. "
                "You may now continue with placement preferences."
            )

            success_message = (
                "The student verification was approved."
            )

        else:
            verification.status = "rejected"
            verification.rejection_reason = (
                rejection_reason
            )

            student_message = (
                "Your student verification was rejected by "
                f"{institution.institution_name}. "
                f"Reason: {rejection_reason}"
            )

            success_message = (
                "The student verification was rejected."
            )

        verification.save(
            update_fields=[
                "status",
                "verified_by",
                "verified_at",
                "rejection_reason",
                "institution_notes",
                "updated_at",
            ]
        )

        Notification.objects.create(
            user=verification.student.user,
            message=student_message,
        )

    messages.success(
        request,
        success_message,
    )

    return redirect(
        "payments:institution_verifications"
    )


def _paid_request_queryset(institution):
    return (
        PlacementAssistanceRequest.objects
        .select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
            "assignment__institution",
            "assignment__school",
            "assignment__department",
            "assignment__programme",
            "verification",
            "matched_opportunity",
            "matched_opportunity__employer",
            "managed_by",
        )
        .filter(
            assignment__institution=institution,
            payment_transactions__status="successful",
        )
        .distinct()
    )


def _matching_terms(*values):
    stop_words = {
        "and",
        "the",
        "for",
        "with",
        "from",
        "this",
        "that",
        "attachment",
        "internship",
    }

    terms = set()

    for value in values:
        if not value:
            continue

        cleaned_value = "".join(
            character.lower()
            if character.isalnum()
            else " "
            for character in str(value)
        )

        terms.update(
            word
            for word in cleaned_value.split()
            if len(word) > 2
            and word not in stop_words
        )

    return terms


def _opportunity_match_score(
    placement_request,
    opportunity,
):
    student = placement_request.student

    student_terms = _matching_terms(
        placement_request.attachment_field,
        student.course,
        student.skills,
        student.extracted_skills,
        student.bio,
    )

    opportunity_terms = _matching_terms(
        opportunity.title,
        opportunity.required_skills,
        opportunity.description,
    )

    overlap_count = len(
        student_terms.intersection(
            opportunity_terms
        )
    )

    score = min(
        70,
        overlap_count * 10,
    )

    preferred_counties = {
        county.strip().lower()
        for county
        in placement_request.preferred_counties.split(",")
        if county.strip()
    }

    opportunity_location = (
        opportunity.location.lower()
    )

    if any(
        county in opportunity_location
        for county in preferred_counties
    ):
        score += 20

    if opportunity.internship_type in {
        "attachment",
        "internship",
    }:
        score += 10

    return min(score, 100)


@login_required
def institution_paid_requests(request):
    institution, access_response = (
        institution_access_check(request)
    )

    if access_response:
        return access_response

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    allowed_statuses = {
        "active",
        "matching",
        "shortlisted",
        "placed",
    }

    requests_query = _paid_request_queryset(
        institution
    )

    if status_filter in allowed_statuses:
        requests_query = requests_query.filter(
            status=status_filter,
        )
    else:
        status_filter = ""

    if search:
        requests_query = requests_query.filter(
            Q(
                assignment__student__full_name__icontains=search
            )
            | Q(
                assignment__student__user__username__icontains=search
            )
            | Q(
                assignment__student__user__email__icontains=search
            )
            | Q(
                assignment__admission_number__icontains=search
            )
            | Q(
                attachment_field__icontains=search
            )
            | Q(
                matched_opportunity__title__icontains=search
            )
        )

    all_requests = _paid_request_queryset(
        institution
    )

    status_counts = {
        "all": all_requests.count(),
        "active": all_requests.filter(
            status="active",
        ).count(),
        "matching": all_requests.filter(
            status="matching",
        ).count(),
        "shortlisted": all_requests.filter(
            status="shortlisted",
        ).count(),
        "placed": all_requests.filter(
            status="placed",
        ).count(),
    }

    paginator = Paginator(
        requests_query.order_by(
            "-activated_at",
            "-created_at",
        ),
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "payments/institution_paid_requests.html",
        {
            "institution": institution,
            "page_obj": page_obj,
            "search": search,
            "status_filter": status_filter,
            "status_counts": status_counts,
            "status_choices": [
                choice
                for choice
                in PlacementAssistanceRequest.STATUS_CHOICES
                if choice[0] in allowed_statuses
            ],
        },
    )


@login_required
def institution_paid_request_detail(
    request,
    request_id,
):
    institution, access_response = (
        institution_access_check(request)
    )

    if access_response:
        return access_response

    placement_request = get_object_or_404(
        _paid_request_queryset(institution),
        id=request_id,
    )

    opportunities = (
        InternshipOpportunity.objects
        .select_related(
            "employer",
        )
        .filter(
            status="open",
            deadline__gte=timezone.localdate(),
            slots_available__gt=0,
        )
        .order_by(
            "deadline",
            "title",
        )
    )

    ranked_opportunities = sorted(
        [
            {
                "opportunity": opportunity,
                "score": _opportunity_match_score(
                    placement_request,
                    opportunity,
                ),
            }
            for opportunity in opportunities
        ],
        key=lambda item: (
            -item["score"],
            item["opportunity"].deadline,
        ),
    )

    return render(
        request,
        "payments/institution_paid_request_detail.html",
        {
            "institution": institution,
            "placement_request": placement_request,
            "student": placement_request.student,
            "assignment": placement_request.assignment,
            "payment": (
                placement_request.successful_payment
            ),
            "ranked_opportunities": (
                ranked_opportunities
            ),
        },
    )


@login_required
def update_paid_request(
    request,
    request_id,
):
    institution, access_response = (
        institution_access_check(request)
    )

    if access_response:
        return access_response

    if request.method != "POST":
        messages.error(
            request,
            "Placement updates must be submitted securely.",
        )

        return redirect(
            "payments:institution_paid_requests"
        )

    action = request.POST.get(
        "action",
        "",
    ).strip().lower()

    institution_notes = request.POST.get(
        "institution_notes",
        "",
    ).strip()

    opportunity_id = request.POST.get(
        "opportunity_id",
        "",
    ).strip()

    allowed_actions = {
        "save_notes",
        "start_matching",
        "shortlist",
        "mark_placed",
        "return_active",
    }

    if action not in allowed_actions:
        messages.error(
            request,
            "Select a valid placement action.",
        )

        return redirect(
            "payments:institution_paid_request_detail",
            request_id=request_id,
        )

    with transaction.atomic():
        placement_request = get_object_or_404(
            PlacementAssistanceRequest.objects
            .select_for_update()
            .select_related(
                "assignment",
                "assignment__student",
                "assignment__student__user",
                "assignment__institution",
                "verification",
                "matched_opportunity",
                "managed_by",
            ),
            id=request_id,
            assignment__institution=institution,
        )

        if not placement_request.is_paid:
            messages.error(
                request,
                "This placement request has no confirmed payment.",
            )

            return redirect(
                "payments:institution_paid_requests"
            )

        opportunity = None

        if opportunity_id:
            opportunity = get_object_or_404(
                InternshipOpportunity.objects
                .select_related("employer"),
                id=opportunity_id,
                status="open",
                deadline__gte=timezone.localdate(),
                slots_available__gt=0,
            )

        if action in {
            "shortlist",
            "mark_placed",
        } and opportunity is None:
            messages.error(
                request,
                (
                    "Select an internship opportunity "
                    "before continuing."
                ),
            )

            return redirect(
                "payments:institution_paid_request_detail",
                request_id=request_id,
            )

        old_status = placement_request.status

        if opportunity is not None:
            placement_request.matched_opportunity = (
                opportunity
            )

        placement_request.managed_by = request.user
        placement_request.institution_notes = (
            institution_notes
        )

        if action == "start_matching":
            placement_request.status = "matching"
        elif action == "shortlist":
            placement_request.status = "shortlisted"
        elif action == "mark_placed":
            placement_request.status = "placed"
        elif action == "return_active":
            placement_request.status = "active"
            placement_request.matched_opportunity = None
            placement_request.matching_started_at = None
            placement_request.shortlisted_at = None
            placement_request.placed_at = None

        placement_request.save()

        if placement_request.status != old_status:
            status_label = (
                placement_request.get_status_display()
            )

            notification_message = (
                "Your placement assistance request is now "
                f"{status_label}."
            )

            if placement_request.matched_opportunity:
                notification_message += (
                    " Selected opportunity: "
                    f"{placement_request.matched_opportunity.title}."
                )

            Notification.objects.create(
                user=placement_request.student.user,
                message=notification_message,
            )

    messages.success(
        request,
        "The placement assistance request was updated.",
    )

    return redirect(
        "payments:institution_paid_request_detail",
        request_id=request_id,
    )
