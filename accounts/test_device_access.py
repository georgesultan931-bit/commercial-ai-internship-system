import json
from types import SimpleNamespace

from django.http import HttpResponse
from django.test import (
    RequestFactory,
    SimpleTestCase,
    override_settings,
)

from .middleware import DeviceAccessMiddleware


TEST_STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}


@override_settings(
    STORAGES=TEST_STORAGES
)
class DeviceAccessMiddlewareTests(SimpleTestCase):

    MOBILE_USER_AGENT = (
        "Mozilla/5.0 "
        "(iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 "
        "Mobile/15E148 Safari/604.1"
    )

    TABLET_USER_AGENT = (
        "Mozilla/5.0 "
        "(iPad; CPU OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 "
        "Mobile/15E148 Safari/604.1"
    )

    ANDROID_USER_AGENT = (
        "Mozilla/5.0 "
        "(Linux; Android 14; SM-A055F) "
        "AppleWebKit/537.36 "
        "Chrome/120.0 "
        "Mobile Safari/537.36"
    )

    DESKTOP_USER_AGENT = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120.0 Safari/537.36"
    )

    def setUp(self):
        self.factory = RequestFactory()

        self.middleware = DeviceAccessMiddleware(
            lambda request: HttpResponse(
                "Dashboard allowed"
            )
        )

    def make_user(
        self,
        role,
        *,
        is_staff=False,
        is_superuser=False,
    ):
        return SimpleNamespace(
            role=role,
            is_authenticated=True,
            is_staff=is_staff,
            is_superuser=is_superuser,
            get_role_display=(
                lambda: (
                    role
                    .replace("_", " ")
                    .title()
                )
            ),
        )

    def make_request(
        self,
        role,
        user_agent,
        *,
        path="/dashboard/",
        is_staff=False,
        is_superuser=False,
        accept="text/html",
    ):
        request = self.factory.get(
            path,
            HTTP_USER_AGENT=user_agent,
            HTTP_ACCEPT=accept,
        )

        request.user = self.make_user(
            role,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

        return request

    def test_student_can_use_phone(self):
        request = self.make_request(
            "student",
            self.MOBILE_USER_AGENT,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Dashboard allowed",
        )

    def test_admin_role_can_use_phone(self):
        request = self.make_request(
            "admin",
            self.MOBILE_USER_AGENT,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_staff_administrator_can_use_phone(self):
        request = self.make_request(
            "",
            self.MOBILE_USER_AGENT,
            is_staff=True,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_superuser_can_use_phone(self):
        request = self.make_request(
            "",
            self.MOBILE_USER_AGENT,
            is_superuser=True,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_employer_is_blocked_on_phone(self):
        request = self.make_request(
            "employer",
            self.MOBILE_USER_AGENT,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertContains(
            response,
            "Desktop or laptop required",
            status_code=403,
        )

    def test_lecturer_is_blocked_on_android_phone(self):
        request = self.make_request(
            "lecturer",
            self.ANDROID_USER_AGENT,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_dean_is_blocked_on_tablet(self):
        request = self.make_request(
            "dean",
            self.TABLET_USER_AGENT,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_restricted_role_can_use_desktop(self):
        request = self.make_request(
            "institution",
            self.DESKTOP_USER_AGENT,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Dashboard allowed",
        )

    def test_restricted_mobile_api_returns_json(self):
        request = self.make_request(
            "supervisor",
            self.MOBILE_USER_AGENT,
            path="/api/private/",
            accept="application/json",
        )

        response = self.middleware(request)

        response_data = json.loads(
            response.content.decode("utf-8")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response_data,
            {
                "detail": (
                    "This account requires "
                    "a desktop or laptop."
                )
            },
        )

    @override_settings(
        DEVICE_ACCESS_RESTRICTION_ENABLED=False
    )
    def test_restriction_can_be_disabled(self):
        request = self.make_request(
            "hod",
            self.MOBILE_USER_AGENT,
        )

        response = self.middleware(request)

        self.assertEqual(
            response.status_code,
            200,
        )