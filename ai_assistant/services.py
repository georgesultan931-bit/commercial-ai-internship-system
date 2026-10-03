import re

from accounts.models import User
from students.models import StudentProfile
from employers.models import EmployerProfile
from internships.models import InternshipOpportunity, Application
from institutions.models import PlacementAssignment, PlacementProgressReport
from supervisors.models import SupervisorProfile

from .gemini_provider import generate_answer, is_configured


def suggested_questions(user):
    role = getattr(user, "role", "")
    options = {
        "student": [
            "What is my application status?",
            "Tell me about my placement.",
            "What is Django?",
            "What can I do in this system?",
        ],
        "employer": [
            "How many applications have I received?",
            "How many opportunities have I posted?",
            "What is Django?",
            "What can I do in this system?",
        ],
        "supervisor": [
            "How many students are assigned to me?",
            "Are there logbooks waiting for review?",
            "What is AI?",
            "What can I do in this system?",
        ],
        "institution": [
            "How many students are under my institution?",
            "How many placements are active?",
            "What is AI?",
            "What can I do in this system?",
        ],
        "admin": [
            "Give me a platform summary.",
            "How many users are registered?",
            "How many applications are there?",
            "Who is president of Kenya right now?",
        ],
    }

    if user.is_staff or user.is_superuser:
        role = "admin"

    return options.get(role, ["What can I do in this system?"])


def _status_counts(qs):
    labels = {}

    for value in (
        "pending",
        "reviewed",
        "shortlisted",
        "interview_scheduled",
        "accepted",
        "rejected",
    ):
        count = qs.filter(status=value).count()
        if count:
            labels[value.replace("_", " ").title()] = count

    return ", ".join(f"{key}: {value}" for key, value in labels.items()) or "No records yet."


def _platform_question(text):
    terms = (
        "my application",
        "my applications",
        "application status",
        "my placement",
        "placement status",
        "my supervisor",
        "my logbook",
        "my reports",
        "my opportunity",
        "my opportunities",
        "my applicants",
        "my candidates",
        "assigned to me",
        "my students",
        "my institution",
        "our institution",
        "our placements",
        "our students",
        "platform summary",
        "registered users",
        "registered accounts",
        "how many users",
        "how many applications",
        "active placements",
        "how many placements",
        "how many opportunities",
        "applications have i received",
        "opportunities have i posted",
        "students are assigned to me",
        "students are under my institution",
    )
    return any(term in text for term in terms)


def _needs_web(text):
    terms = (
        "right now",
        "currently",
        "current ",
        "today",
        "tonight",
        "latest",
        "recent",
        "this week",
        "this month",
        "this year",
        "news",
        "president",
        "prime minister",
        "governor",
        "ceo",
        "price",
        "exchange rate",
        "weather",
        "score",
        "winner",
        "election",
        "stock",
        "market",
        "live",
        "2026",
    )
    return any(term in text for term in terms)


def _local_answer(user, text):
    role = getattr(user, "role", "")
    is_admin = role == "admin" or user.is_staff or user.is_superuser

    if role == "student":
        profile = StudentProfile.objects.filter(user=user).first()

        if not profile:
            return "Your student profile has not been created yet."

        if "application" in text:
            qs = Application.objects.filter(student=profile)
            return (
                f"You have {qs.count()} application(s). "
                f"Status summary: {_status_counts(qs)}"
            )

        if "placement" in text or "supervisor" in text or "logbook" in text:
            assignment = (
                PlacementAssignment.objects.filter(student=profile)
                .select_related("institution", "supervisor")
                .order_by("-created_at")
                .first()
            )

            if not assignment:
                return "You do not currently have a placement assignment."

            supervisor = (
                assignment.supervisor.full_name
                if assignment.supervisor
                else "Not assigned"
            )

            return (
                f"Your latest placement status is "
                f"{assignment.get_status_display()}. "
                f"Supervisor: {supervisor}."
            )

    if role == "employer":
        profile = EmployerProfile.objects.filter(user=user).first()

        if not profile:
            return "Your employer profile has not been created yet."

        opportunities = InternshipOpportunity.objects.filter(employer=profile)
        applications = Application.objects.filter(
            opportunity__employer=profile
        )

        if (
            "application" in text
            or "applicant" in text
            or "candidate" in text
        ):
            return (
                f"Your opportunities have received "
                f"{applications.count()} application(s). "
                f"Status summary: {_status_counts(applications)}"
            )

        if "opportunit" in text:
            return (
                f"You have posted {opportunities.count()} "
                f"opportunity/opportunities; "
                f"{opportunities.filter(status='open').count()} are open."
            )

    if role == "supervisor":
        profile = SupervisorProfile.objects.filter(user=user).first()

        if not profile:
            return "Your supervisor profile has not been created yet."

        assignments = PlacementAssignment.objects.filter(
            supervisor=profile
        )

        if "student" in text or "placement" in text:
            return (
                f"You have {assignments.count()} assigned placement(s); "
                f"{assignments.filter(status__in=['assigned', 'ongoing']).count()} "
                f"are active/assigned and "
                f"{assignments.filter(status='completed').count()} completed."
            )

        if "logbook" in text or "report" in text:
            reports = PlacementProgressReport.objects.filter(
                assignment__supervisor=profile
            )
            return (
                f"There are {reports.count()} progress report(s) "
                f"linked to your assigned students."
            )

    if role == "institution":
        profile = getattr(user, "institution_profile", None)

        if not profile:
            try:
                from institutions.models import InstitutionProfile

                profile = InstitutionProfile.objects.filter(
                    user=user
                ).first()
            except Exception:
                profile = None

        if not profile:
            return "Your institution profile has not been created yet."

        students = StudentProfile.objects.filter(
            institution_profile=profile
        )
        assignments = PlacementAssignment.objects.filter(
            institution=profile
        )

        if "student" in text:
            return (
                f"Your institution has {students.count()} linked "
                f"student profile(s) and {assignments.count()} "
                f"placement assignment(s)."
            )

        if "placement" in text:
            return (
                f"Your institution has {assignments.count()} placement(s); "
                f"{assignments.filter(status__in=['assigned', 'ongoing']).count()} "
                f"are active/assigned."
            )

    if is_admin:
        accounts = User.objects.filter(
            role__in=[
                "student",
                "employer",
                "institution",
                "supervisor",
            ]
        )

        if "user" in text or "account" in text:
            return (
                f"There are {accounts.count()} registered "
                f"student/professional accounts."
            )

        if "application" in text:
            qs = Application.objects.all()
            return (
                f"The platform has {qs.count()} application(s). "
                f"Status summary: {_status_counts(qs)}"
            )

        if "placement" in text:
            qs = PlacementAssignment.objects.all()
            return (
                f"The platform has {qs.count()} placement assignment(s): "
                f"{qs.filter(status__in=['assigned', 'ongoing']).count()} "
                f"active/assigned and "
                f"{qs.filter(status='completed').count()} completed."
            )

        if "summary" in text or "platform" in text:
            return (
                f"Platform summary: "
                f"{StudentProfile.objects.count()} student profile(s), "
                f"{EmployerProfile.objects.count()} employer profile(s), "
                f"{InternshipOpportunity.objects.count()} "
                f"opportunity/opportunities, "
                f"{Application.objects.count()} application(s), and "
                f"{PlacementAssignment.objects.count()} "
                f"placement assignment(s)."
            )

    return "I can help with your permitted platform information."


def _provider_failure_answer(result, use_web):
    """
    Convert the provider's structured failure into a safe user-facing message.

    Current/time-sensitive questions must never silently fall back to an
    ungrounded model answer when live grounding is unavailable.
    """
    error_code = result.get("error_code", "")
    provider_message = (result.get("error_message") or "").strip()

    if error_code == "grounding_quota":
        return (
            provider_message
            or (
                "Live search is temporarily unavailable because the current "
                "AI/search quota has been reached. I can still answer general "
                "questions, but I cannot safely verify current information "
                "right now."
            )
        )

    if use_web and error_code in {
        "timeout",
        "connection_error",
        "request_error",
        "authentication",
        "model_unavailable",
        "provider_error",
        "invalid_response",
        "empty_response",
        "quota",
    }:
        return (
            "I can't verify that current information right now because live "
            "search is temporarily unavailable. Please try again later."
        )

    if provider_message:
        return provider_message

    return (
        "The general AI service is temporarily unavailable. "
        "Please try again shortly."
    )


def answer_for_user(user, message):
    cleaned = re.sub(r"\s+", " ", (message or "").strip())
    text = cleaned.lower()

    if not cleaned:
        return {
            "answer": "Type a question and I will help.",
            "source": "assistant",
            "sources": [],
        }

    # Private/platform questions stay inside Django and are never sent to
    # Gemini. Existing role/tenant scoping remains authoritative.
    if _platform_question(text):
        return {
            "answer": _local_answer(user, text),
            "source": "platform",
            "sources": [],
        }

    if not is_configured():
        return {
            "answer": (
                "The general AI service is not configured right now. "
                "Platform-specific assistance is still available."
            ),
            "source": "fallback",
            "sources": [],
        }

    use_web = _needs_web(text)
    result = generate_answer(cleaned, use_web=use_web)

    if result.get("ok"):
        return {
            "answer": result.get("answer", ""),
            "source": "web" if use_web else "gemini",
            "sources": result.get("sources") or [],
        }

    return {
        "answer": _provider_failure_answer(result, use_web),
        "source": "fallback",
        "sources": [],
    }
