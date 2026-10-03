from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.urls import Resolver404, resolve


class DeviceAccessMiddleware:
    """
    Allow students and administrators to use any device.

    Employer, institution, supervisor, lecturer, HOD and dean
    accounts require a desktop or laptop.
    """

    DEFAULT_MOBILE_ALLOWED_ROLES = {
        "student",
        "admin",
    }

    MOBILE_DEVICE_KEYWORDS = (
        "android",
        "iphone",
        "ipad",
        "ipod",
        "windows phone",
        "blackberry",
        "opera mini",
        "opera mobi",
        "mobile",
        "tablet",
        "kindle",
        "silk/",
        "playbook",
    )

    EXEMPT_URL_NAMES = {
        "login",
        "logout",
        "password_reset",
        "password_reset_done",
        "password_reset_confirm",
        "password_reset_complete",
        "verify_otp",
        "pending_approval",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_restrict_request(request):
            if self._expects_json(request):
                return JsonResponse(
                    {
                        "detail": (
                            "This account requires a desktop or laptop."
                        )
                    },
                    status=403,
                )

            content = render_to_string(
                "accounts/desktop_required.html",
                {
                    "account_role": self._role_label(
                        request.user
                    ),
                },
            )

            return HttpResponse(
                content,
                status=403,
            )

        return self.get_response(request)

    def _should_restrict_request(self, request):
        restriction_enabled = getattr(
            settings,
            "DEVICE_ACCESS_RESTRICTION_ENABLED",
            True,
        )

        if not restriction_enabled:
            return False

        user = getattr(
            request,
            "user",
            None,
        )

        if not user:
            return False

        if not user.is_authenticated:
            return False

        if self._is_exempt_request(request):
            return False

        if user.is_superuser or user.is_staff:
            return False

        allowed_roles = set(
            getattr(
                settings,
                "MOBILE_ALLOWED_ROLES",
                self.DEFAULT_MOBILE_ALLOWED_ROLES,
            )
        )

        role = str(
            getattr(
                user,
                "role",
                "",
            )
        ).strip().lower()

        if role in allowed_roles:
            return False

        return self._is_mobile_or_tablet(request)

    def _is_mobile_or_tablet(self, request):
        user_agent = request.META.get(
            "HTTP_USER_AGENT",
            "",
        ).lower()

        if not user_agent:
            return False

        return any(
            keyword in user_agent
            for keyword in self.MOBILE_DEVICE_KEYWORDS
        )

    def _is_exempt_request(self, request):
        path = request.path_info

        exempt_prefixes = (
            settings.STATIC_URL,
            settings.MEDIA_URL,
        )

        if any(
            prefix
            and path.startswith(prefix)
            for prefix in exempt_prefixes
        ):
            return True

        try:
            match = resolve(path)
        except Resolver404:
            return False

        return (
            match.url_name
            in self.EXEMPT_URL_NAMES
        )

    def _expects_json(self, request):
        path = request.path_info

        accept_header = request.headers.get(
            "Accept",
            "",
        )

        return (
            path.startswith("/api/")
            or "application/json"
            in accept_header.lower()
        )

    def _role_label(self, user):
        get_role_display = getattr(
            user,
            "get_role_display",
            None,
        )

        if callable(get_role_display):
            return get_role_display()

        role = str(
            getattr(
                user,
                "role",
                "Professional",
            )
        )

        return (
            role
            .replace("_", " ")
            .title()
        )