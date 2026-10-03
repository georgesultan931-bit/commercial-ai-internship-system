from django.core.exceptions import ObjectDoesNotExist

from payments.models import StudentVerification

from .models import Notification


def _image_url(image_field):
    if not image_field:
        return ""

    try:
        return image_field.url
    except ValueError:
        return ""


def _dashboard_profile_image_url(user):
    if user.role == "student":
        try:
            student_profile = user.studentprofile
        except ObjectDoesNotExist:
            student_profile = None

        image_url = _image_url(
            getattr(
                student_profile,
                "profile_picture",
                None,
            )
        )

        if image_url:
            return image_url

    if user.role == "employer":
        try:
            employer_profile = user.employerprofile
        except ObjectDoesNotExist:
            employer_profile = None

        image_url = _image_url(
            getattr(
                employer_profile,
                "logo",
                None,
            )
        )

        if image_url:
            return image_url

    if user.role == "institution":
        try:
            institution_profile = (
                user.institution_profile
            )
        except ObjectDoesNotExist:
            institution_profile = None

        image_url = _image_url(
            getattr(
                institution_profile,
                "logo",
                None,
            )
        )

        if image_url:
            return image_url

    return _image_url(
        getattr(
            user,
            "profile_picture",
            None,
        )
    )


def _pending_student_verifications(user):
    if user.role != "institution":
        return 0

    try:
        institution = user.institution_profile
    except ObjectDoesNotExist:
        return 0

    return (
        StudentVerification.objects
        .filter(
            assignment__institution=institution,
            status="pending",
        )
        .count()
    )


def notification_count(request):
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "unread_notifications": 0,
            "recent_notifications": [],
            "pending_student_verifications": 0,
            "dashboard_profile_image_url": "",
        }

    user_notifications = (
        Notification.objects
        .filter(
            user=request.user,
        )
        .order_by(
            "-created_at",
        )
    )

    unread_count = (
        user_notifications
        .filter(
            is_read=False,
        )
        .count()
    )

    return {
        "unread_notifications_count": unread_count,
        "unread_notifications": unread_count,
        "recent_notifications": (
            user_notifications[:5]
        ),
        "pending_student_verifications": (
            _pending_student_verifications(
                request.user
            )
        ),
        "dashboard_profile_image_url": (
            _dashboard_profile_image_url(
                request.user
            )
        ),
    }