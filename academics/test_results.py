from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from institutions.models import InstitutionProfile
from notifications.models import Notification
from students.models import StudentProfile

from .models import (
    AcademicStaffProfile,
    AcademicYear,
    Department,
    GradeAmendmentRequest,
    GradeAuditLog,
    GradeBand,
    GradeScale,
    Programme,
    SchoolFaculty,
    Semester,
    SemesterResultSubmission,
    StudentAcademicAssignment,
    StudentGrade,
    StudentUnitRegistration,
    Unit,
)


class AcademicResultWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.institution_user = user_model.objects.create_user(
            username="test_institution",
            email="institution-results@example.com",
            password="TestPass123!",
            role="institution",
            is_active=True,
            is_approved=True,
        )
        self.institution = InstitutionProfile.objects.create(
            user=self.institution_user,
            institution_name="Test University",
            institution_type="university",
            is_verified=True,
        )
        self.school = SchoolFaculty.objects.create(
            institution=self.institution,
            name="School of Computing",
            code="SOC",
        )
        self.department = Department.objects.create(
            school=self.school,
            name="Department of Computer Science",
            code="CS",
        )
        self.programme = Programme.objects.create(
            department=self.department,
            name="Bachelor of Computer Science",
            code="BCS",
            qualification_level="Bachelor",
            duration_years=4,
        )

        self.hod = user_model.objects.create_user(
            username="test_hod",
            email="hod-results@example.com",
            password="TestPass123!",
            role="hod",
            is_active=True,
            is_approved=True,
        )
        AcademicStaffProfile.objects.create(
            user=self.hod,
            institution=self.institution,
            school=self.school,
            department=self.department,
            academic_role="hod",
            staff_number="HOD001",
        )

        self.dean = user_model.objects.create_user(
            username="test_dean",
            email="dean-results@example.com",
            password="TestPass123!",
            role="dean",
            is_active=True,
            is_approved=True,
        )
        AcademicStaffProfile.objects.create(
            user=self.dean,
            institution=self.institution,
            school=self.school,
            department=None,
            academic_role="dean",
            staff_number="DEAN001",
        )

        self.student_user = user_model.objects.create_user(
            username="test_student",
            email="student-results@example.com",
            password="TestPass123!",
            role="student",
            is_active=True,
            is_approved=True,
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            first_name="Test",
            surname="Student",
            institution_profile=self.institution,
            course="Bachelor of Computer Science",
        )
        self.assignment = StudentAcademicAssignment.objects.create(
            student=self.student,
            institution=self.institution,
            school=self.school,
            department=self.department,
            programme=self.programme,
            admission_number="CS-TEST-001",
            year_of_study=2,
        )

        self.academic_year = AcademicYear.objects.create(
            institution=self.institution,
            name="2026/2027",
            starts_on=date(2026, 9, 1),
            ends_on=date(2027, 8, 31),
            is_current=True,
        )
        self.semester = Semester.objects.create(
            academic_year=self.academic_year,
            name="Semester 1",
            number=1,
            starts_on=date(2026, 9, 1),
            ends_on=date(2026, 12, 20),
            is_current=True,
        )
        self.unit = Unit.objects.create(
            programme=self.programme,
            code="CSC201",
            title="Data Structures and Algorithms",
            year_of_study=2,
            semester_number=1,
            credit_hours=Decimal("3.0"),
        )

        self.scale = GradeScale.objects.create(
            institution=self.institution,
            name="Default CAT 30 Exam 70",
            coursework_weight=Decimal("30.00"),
            examination_weight=Decimal("70.00"),
            pass_mark=Decimal("40.00"),
            is_default=True,
            created_by=self.hod,
        )
        bands = (
            ("70.00", "100.00", "A", "4.00", "Excellent", True),
            ("60.00", "69.99", "B", "3.00", "Very Good", True),
            ("50.00", "59.99", "C", "2.00", "Good", True),
            ("40.00", "49.99", "D", "1.00", "Pass", True),
            ("0.00", "39.99", "E", "0.00", "Fail", False),
        )
        for minimum, maximum, letter, points, remark, is_pass in bands:
            GradeBand.objects.create(
                scale=self.scale,
                minimum_mark=Decimal(minimum),
                maximum_mark=Decimal(maximum),
                letter_grade=letter,
                grade_point=Decimal(points),
                remark=remark,
                is_pass=is_pass,
            )

        self.submission = SemesterResultSubmission.objects.create(
            assignment=self.assignment,
            semester=self.semester,
            grading_scale=self.scale,
            status="draft",
        )
        self.registration = StudentUnitRegistration.objects.create(
            assignment=self.assignment,
            unit=self.unit,
            semester=self.semester,
            study_year=2,
            registered_by=self.hod,
        )
        self.grade = StudentGrade.objects.create(
            registration=self.registration,
            submission=self.submission,
            coursework_mark=Decimal("30.00"),
            examination_mark=Decimal("35.00"),
            entered_by=self.hod,
        )

    def publish_submission(self):
        now = timezone.now()
        self.submission.status = "published"
        self.submission.submitted_by = self.hod
        self.submission.submitted_at = now
        self.submission.reviewed_by = self.dean
        self.submission.reviewed_at = now
        self.submission.published_at = now
        self.submission.save()

    def request_amendment(self, examination_mark="40.00"):
        self.client.force_login(self.hod)
        response = self.client.post(
            reverse(
                "academics:request_grade_amendment",
                args=[self.grade.pk],
            ),
            {
                "proposed_coursework_mark": "30.00",
                "proposed_examination_mark": examination_mark,
                "reason": "The examination mark was entered incorrectly.",
            },
        )
        self.assertEqual(response.status_code, 302)
        return GradeAmendmentRequest.objects.get(grade=self.grade)

    def test_grade_calculation_uses_institution_scale(self):
        self.grade.refresh_from_db()

        self.assertEqual(self.grade.total_mark, Decimal("65.00"))
        self.assertEqual(self.grade.letter_grade, "B")
        self.assertEqual(self.grade.grade_point, Decimal("3.00"))
        self.assertEqual(self.grade.remark, "Very Good")
        self.assertTrue(self.grade.is_pass)

    def test_student_cannot_open_hod_grade_management(self):
        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("academics:hod_result_students")
        )

        self.assertEqual(response.status_code, 403)

    def test_hod_submits_complete_results_and_notifies_dean(self):
        self.client.force_login(self.hod)

        response = self.client.post(
            reverse(
                "academics:submit_results_to_dean",
                args=[self.submission.pk],
            ),
            {"submit-confirmation": "on"},
        )

        self.assertEqual(response.status_code, 302)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, "submitted")
        self.assertEqual(self.submission.submitted_by, self.hod)
        self.assertIsNotNone(self.submission.submitted_at)
        self.assertTrue(
            GradeAuditLog.objects.filter(
                submission=self.submission,
                action="submitted",
                actor=self.hod,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.dean,
                message__icontains="submitted",
            ).exists()
        )

    def test_dean_publishes_and_student_can_download_documents(self):
        now = timezone.now()
        self.submission.status = "submitted"
        self.submission.submitted_by = self.hod
        self.submission.submitted_at = now
        self.submission.save()

        self.client.force_login(self.dean)
        response = self.client.post(
            reverse(
                "academics:dean_review_results",
                args=[self.submission.pk],
            ),
            {"action": "publish", "review_notes": "Verified and approved."},
        )

        self.assertEqual(response.status_code, 302)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, "published")
        self.assertEqual(self.submission.reviewed_by, self.dean)
        self.assertIsNotNone(self.submission.published_at)
        self.assertTrue(
            Notification.objects.filter(
                user=self.student_user,
                message__icontains="available for download",
            ).exists()
        )

        self.client.force_login(self.student_user)
        results_response = self.client.get(
            reverse("academics:my_academic_results")
        )
        self.assertEqual(results_response.status_code, 200)
        self.assertContains(results_response, "CSC201")
        self.assertContains(results_response, "65.00")

        slip_response = self.client.get(
            reverse(
                "academics:download_result_slip",
                args=[self.submission.pk],
            )
        )
        self.assertEqual(slip_response.status_code, 200)
        self.assertEqual(slip_response["Content-Type"], "application/pdf")

        transcript_response = self.client.get(
            reverse("academics:download_transcript")
        )
        self.assertEqual(transcript_response.status_code, 200)
        self.assertEqual(
            transcript_response["Content-Type"],
            "application/pdf",
        )

    def test_dean_approval_applies_amendment_and_creates_audit_log(self):
        self.publish_submission()
        amendment = self.request_amendment(examination_mark="40.00")

        self.client.force_login(self.dean)
        response = self.client.post(
            reverse(
                "academics:dean_review_amendment",
                args=[amendment.pk],
            ),
            {"action": "approve", "review_notes": "Evidence verified."},
        )

        self.assertEqual(response.status_code, 302)
        amendment.refresh_from_db()
        self.grade.refresh_from_db()
        self.assertEqual(amendment.status, "approved")
        self.assertEqual(amendment.reviewed_by, self.dean)
        self.assertIsNotNone(amendment.applied_at)
        self.assertEqual(self.grade.examination_mark, Decimal("40.00"))
        self.assertEqual(self.grade.total_mark, Decimal("70.00"))
        self.assertEqual(self.grade.letter_grade, "A")
        self.assertTrue(
            GradeAuditLog.objects.filter(
                grade=self.grade,
                submission=self.submission,
                action="amended",
                actor=self.dean,
            ).exists()
        )

    def test_dean_rejection_does_not_change_published_grade(self):
        self.publish_submission()
        amendment = self.request_amendment(examination_mark="40.00")

        self.client.force_login(self.dean)
        response = self.client.post(
            reverse(
                "academics:dean_review_amendment",
                args=[amendment.pk],
            ),
            {
                "action": "reject",
                "review_notes": "Supporting evidence was not sufficient.",
            },
        )

        self.assertEqual(response.status_code, 302)
        amendment.refresh_from_db()
        self.grade.refresh_from_db()
        self.assertEqual(amendment.status, "rejected")
        self.assertEqual(amendment.reviewed_by, self.dean)
        self.assertIsNone(amendment.applied_at)
        self.assertEqual(self.grade.examination_mark, Decimal("35.00"))
        self.assertEqual(self.grade.total_mark, Decimal("65.00"))
        self.assertEqual(self.grade.letter_grade, "B")
        self.assertFalse(
            GradeAuditLog.objects.filter(
                grade=self.grade,
                action="amended",
            ).exists()
        )
