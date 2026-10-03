from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from students.models import StudentProfile
from supervisors.models import SupervisorProfile

from .models import InstitutionProfile, PlacementAssignment


User = get_user_model()


class PlacementSecurityTests(TestCase):
    """
    Cross-tenant and cross-role security tests for institution,
    supervisor, and student placement access.
    """

    def setUp(self):
        self.password = "TestPass123!"

        # Institution A
        self.institution_user_a = User.objects.create_user(
            username="institution_a",
            email="institution-a@example.com",
            password=self.password,
            role="institution",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        self.institution_a = InstitutionProfile.objects.create(
            user=self.institution_user_a,
            institution_name="Kabarak University",
            official_email="institution-a@example.com",
            phone_number="0700000001",
        )

        # Institution B
        self.institution_user_b = User.objects.create_user(
            username="institution_b",
            email="institution-b@example.com",
            password=self.password,
            role="institution",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        self.institution_b = InstitutionProfile.objects.create(
            user=self.institution_user_b,
            institution_name="Maseno University",
            official_email="institution-b@example.com",
            phone_number="0700000002",
        )

        # Student A
        self.student_user_a = User.objects.create_user(
            username="student_a",
            email="student-a@example.com",
            password=self.password,
            role="student",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        self.student_a = StudentProfile.objects.create(
            user=self.student_user_a,
            first_name="Student",
            surname="Alpha",
            course="Computer Science",
            institution_profile=self.institution_a,
        )

        # Student B
        self.student_user_b = User.objects.create_user(
            username="student_b",
            email="student-b@example.com",
            password=self.password,
            role="student",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        self.student_b = StudentProfile.objects.create(
            user=self.student_user_b,
            first_name="Student",
            surname="Beta",
            course="Information Technology",
            institution_profile=self.institution_b,
        )

        # Supervisor A
        self.supervisor_user_a = User.objects.create_user(
            username="supervisor_a",
            email="supervisor-a@example.com",
            password=self.password,
            role="supervisor",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        self.supervisor_a = SupervisorProfile.objects.create(
            user=self.supervisor_user_a,
            institution=self.institution_a,
            full_name="Supervisor Alpha",
            official_email="supervisor-a@example.com",
            phone_number="0710000001",
        )

        # Supervisor B
        self.supervisor_user_b = User.objects.create_user(
            username="supervisor_b",
            email="supervisor-b@example.com",
            password=self.password,
            role="supervisor",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        self.supervisor_b = SupervisorProfile.objects.create(
            user=self.supervisor_user_b,
            institution=self.institution_b,
            full_name="Supervisor Beta",
            official_email="supervisor-b@example.com",
            phone_number="0710000002",
        )

        # Placement belonging to Institution A
        self.assignment_a = PlacementAssignment.objects.create(
            institution=self.institution_a,
            student=self.student_a,
            supervisor=self.supervisor_a,
            status="ongoing",
        )

        # Placement belonging to Institution B
        self.assignment_b = PlacementAssignment.objects.create(
            institution=self.institution_b,
            student=self.student_b,
            supervisor=self.supervisor_b,
            status="ongoing",
        )

    def login_as(self, user):
        logged_in = self.client.login(
            username=user.username,
            password=self.password,
        )
        self.assertTrue(logged_in)

    def test_institution_student_list_only_contains_own_assignments(self):
        self.login_as(self.institution_user_a)

        response = self.client.get(
            reverse("institution_students")
        )

        self.assertEqual(response.status_code, 200)

        assignments = list(
            response.context["assignments"]
        )

        self.assertIn(
            self.assignment_a,
            assignments,
        )

        self.assertNotIn(
            self.assignment_b,
            assignments,
        )

    def test_institution_cannot_edit_another_institutions_assignment(self):
        self.login_as(self.institution_user_a)

        response = self.client.get(
            reverse(
                "edit_placement_assignment",
                args=[self.assignment_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_institution_cannot_view_another_institutions_placement_detail(self):
        self.login_as(self.institution_user_a)

        response = self.client.get(
            reverse(
                "institution_placement_detail",
                args=[self.assignment_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_supervisor_only_sees_own_assigned_students(self):
        self.login_as(self.supervisor_user_a)

        response = self.client.get(
            reverse("supervisor_assigned_students")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        assignments = list(
            response.context["assignments"]
        )

        self.assertIn(
            self.assignment_a,
            assignments,
        )

        self.assertNotIn(
            self.assignment_b,
            assignments,
        )

    def test_supervisor_cannot_view_another_supervisors_assignment(self):
        self.login_as(self.supervisor_user_a)

        response = self.client.get(
            reverse(
                "supervisor_student_detail",
                args=[self.assignment_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_student_cannot_view_another_students_logbook(self):
        self.login_as(self.student_user_a)

        response = self.client.get(
            reverse(
                "placement_logbook",
                args=[self.assignment_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_student_my_placement_only_contains_own_assignment(self):
        self.login_as(self.student_user_a)

        response = self.client.get(
            reverse("my_placement")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        assignments = list(
            response.context["assignments"]
        )

        self.assertIn(
            self.assignment_a,
            assignments,
        )

        self.assertNotIn(
            self.assignment_b,
            assignments,
        )

    def test_institution_reports_do_not_include_other_institutions_data(self):
        self.login_as(self.institution_user_a)

        response = self.client.get(
            reverse("institution_reports")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        # The institution reports page should only count
        # placements belonging to the logged-in institution.
        if "total_assignments" in response.context:
            self.assertEqual(
                response.context["total_assignments"],
                1,
            )

        if "total_placements" in response.context:
            self.assertEqual(
                response.context["total_placements"],
                1,
            )

        # Strong content-level isolation check.
        response_text = response.content.decode(
            "utf-8",
            errors="ignore",
        )

        self.assertNotIn(
            self.student_b.user.username,
            response_text,
        )

        self.assertNotIn(
            self.supervisor_b.full_name,
            response_text,
        )


class PlacementRelationshipTests(TestCase):
    """
    Tests for the new StudentProfile -> InstitutionProfile relationship.
    """

    def setUp(self):
        self.password = "TestPass123!"

        self.institution_user = User.objects.create_user(
            username="relationship_institution",
            email="relationship-institution@example.com",
            password=self.password,
            role="institution",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        self.institution = InstitutionProfile.objects.create(
            user=self.institution_user,
            institution_name="Relationship Test University",
            official_email="relationship-institution@example.com",
            phone_number="0720000001",
        )

        self.student_user = User.objects.create_user(
            username="relationship_student",
            email="relationship-student@example.com",
            password=self.password,
            role="student",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

    def test_student_institution_text_is_synchronised_from_fk(self):
        student = StudentProfile.objects.create(
            user=self.student_user,
            first_name="Relationship",
            surname="Student",
            course="Computer Science",
            institution_profile=self.institution,
        )

        student.refresh_from_db()

        self.assertEqual(
            student.institution_profile,
            self.institution,
        )

        self.assertEqual(
            student.institution,
            self.institution.institution_name,
        )
