from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AcademicRouteTests(TestCase):
    """Confirm that every academic route is registered correctly."""

    EXPECTED_ROUTES = {
        "academics:dashboard": "/academics/dashboard/",
        "academics:department_students": "/academics/students/",
        "academics:department_supervisors": "/academics/supervisors/",
        "academics:department_applications": "/academics/applications/",
        "academics:department_internships": "/academics/internships/",
        "academics:academic_reports": "/academics/reports/",
        "academics:school_departments": "/academics/school/departments/",
        "academics:school_students": "/academics/school/students/",
        "academics:school_supervisors": "/academics/school/supervisors/",
        "academics:school_internships": "/academics/school/internships/",
        "academics:school_applications": "/academics/school/applications/",
    }

    def test_all_academic_route_names_resolve(self):
        for route_name, expected_path in self.EXPECTED_ROUTES.items():
            with self.subTest(route_name=route_name):
                self.assertEqual(reverse(route_name), expected_path)

    def test_anonymous_users_are_sent_to_login(self):
        for route_name in self.EXPECTED_ROUTES:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login/", response.url)


class AcademicRoleAccessTests(TestCase):
    """Verify HOD and Dean pages cannot be crossed between roles."""

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username="access_student",
            email="access-student@example.com",
            password="TestPass123!",
            role="student",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        cls.hod = User.objects.create_user(
            username="access_hod",
            email="access-hod@example.com",
            password="TestPass123!",
            role="hod",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        cls.dean = User.objects.create_user(
            username="access_dean",
            email="access-dean@example.com",
            password="TestPass123!",
            role="dean",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

    def assert_redirected(self, user, route_name):
        self.client.force_login(user)
        response = self.client.get(reverse(route_name))
        self.assertEqual(response.status_code, 302)
        self.client.logout()

    def assert_pending_assignment(self, user, route_name):
        self.client.force_login(user)
        response = self.client.get(reverse(route_name))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "academics/assignment_pending.html")
        self.client.logout()

    def test_student_cannot_access_academic_dashboard(self):
        self.assert_redirected(self.student, "academics:dashboard")

    def test_student_cannot_access_hod_or_dean_pages(self):
        restricted_routes = (
            "academics:department_students",
            "academics:department_supervisors",
            "academics:department_applications",
            "academics:department_internships",
            "academics:academic_reports",
            "academics:school_departments",
            "academics:school_students",
            "academics:school_supervisors",
            "academics:school_internships",
            "academics:school_applications",
        )

        for route_name in restricted_routes:
            with self.subTest(route_name=route_name):
                self.assert_redirected(self.student, route_name)

    def test_hod_cannot_access_dean_pages(self):
        dean_routes = (
            "academics:school_departments",
            "academics:school_students",
            "academics:school_supervisors",
            "academics:school_internships",
            "academics:school_applications",
        )

        for route_name in dean_routes:
            with self.subTest(route_name=route_name):
                self.assert_redirected(self.hod, route_name)

    def test_dean_cannot_access_hod_pages(self):
        hod_routes = (
            "academics:department_students",
            "academics:department_supervisors",
            "academics:department_applications",
            "academics:department_internships",
        )

        for route_name in hod_routes:
            with self.subTest(route_name=route_name):
                self.assert_redirected(self.dean, route_name)

    def test_hod_without_assignment_sees_pending_page(self):
        routes = (
            "academics:dashboard",
            "academics:department_students",
            "academics:department_supervisors",
            "academics:department_applications",
            "academics:department_internships",
            "academics:academic_reports",
        )

        for route_name in routes:
            with self.subTest(route_name=route_name):
                self.assert_pending_assignment(self.hod, route_name)

    def test_dean_without_assignment_sees_pending_page(self):
        routes = (
            "academics:dashboard",
            "academics:school_departments",
            "academics:school_students",
            "academics:school_supervisors",
            "academics:school_internships",
            "academics:school_applications",
            "academics:academic_reports",
        )

        for route_name in routes:
            with self.subTest(route_name=route_name):
                self.assert_pending_assignment(self.dean, route_name)
