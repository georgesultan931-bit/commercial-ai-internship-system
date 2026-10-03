from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from institutions.models import InstitutionProfile
from notifications.models import Notification
from students.models import StudentProfile

from .models import (
    AcademicStaffProfile,
    AcademicYear,
    Department,
    GradeBand,
    GradeScale,
    LecturerResultSheet,
    LecturerResultSheetAuditLog,
    LecturerUnitAssignment,
    Programme,
    SchoolFaculty,
    Semester,
    SemesterResultSubmission,
    StudentAcademicAssignment,
    StudentGrade,
    StudentUnitRegistration,
    Unit,
)


class LecturerResultWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        password = "TestPass123!"

        institution_user = user_model.objects.create_user(
            username="lecturer_test_institution",
            email="lecturer-institution@example.com",
            password=password,
            role="institution",
            is_active=True,
            is_approved=True,
        )
        self.institution = InstitutionProfile.objects.create(
            user=institution_user,
            institution_name="Lecturer Test University",
            institution_type="university",
            is_verified=True,
        )
        self.school = SchoolFaculty.objects.create(
            institution=self.institution,
            name="School of Technology",
            code="SOT",
        )
        self.department = Department.objects.create(
            school=self.school,
            name="Department of Computing",
            code="DOC",
        )
        self.programme = Programme.objects.create(
            department=self.department,
            name="Bachelor of Computing",
            code="BCOMP",
            qualification_level="Bachelor",
            duration_years=4,
        )

        self.hod = user_model.objects.create_user(
            username="lecturer_test_hod",
            email="lecturer-hod@example.com",
            password=password,
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
        )

        self.lecturer = user_model.objects.create_user(
            username="lecturer_test_user",
            email="lecturer@example.com",
            password=password,
            role="lecturer",
            is_active=True,
            is_approved=True,
        )
        self.lecturer_profile = AcademicStaffProfile.objects.create(
            user=self.lecturer,
            institution=self.institution,
            school=self.school,
            department=self.department,
            academic_role="lecturer",
            staff_number="LEC001",
        )

        self.student_user = user_model.objects.create_user(
            username="lecturer_test_student",
            email="lecturer-student@example.com",
            password=password,
            role="student",
            is_active=True,
            is_approved=True,
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            first_name="Lecturer",
            surname="Student",
            institution_profile=self.institution,
            course="Bachelor of Computing",
        )
        self.student_assignment = StudentAcademicAssignment.objects.create(
            student=self.student,
            institution=self.institution,
            school=self.school,
            department=self.department,
            programme=self.programme,
            admission_number="LEC-TEST-001",
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
            code="CSC210",
            title="Algorithms",
            year_of_study=2,
            semester_number=1,
            credit_hours=Decimal("3.0"),
        )
        self.lecturer_assignment = LecturerUnitAssignment.objects.create(
            lecturer=self.lecturer_profile,
            unit=self.unit,
            semester=self.semester,
            assigned_by=institution_user,
        )
        self.registration = StudentUnitRegistration.objects.create(
            assignment=self.student_assignment,
            unit=self.unit,
            semester=self.semester,
            study_year=2,
            registered_by=self.hod,
        )

        self.scale = GradeScale.objects.create(
            institution=self.institution,
            name="CAT 30 Exam 70",
            coursework_weight=Decimal("30.00"),
            examination_weight=Decimal("70.00"),
            pass_mark=Decimal("40.00"),
            is_default=True,
            created_by=self.hod,
        )
        for values in (
            ("70.00", "100.00", "A", "4.00", "Excellent", True),
            ("60.00", "69.99", "B", "3.00", "Very Good", True),
            ("50.00", "59.99", "C", "2.00", "Good", True),
            ("40.00", "49.99", "D", "1.00", "Pass", True),
            ("0.00", "39.99", "E", "0.00", "Fail", False),
        ):
            minimum, maximum, letter, points, remark, is_pass = values
            GradeBand.objects.create(
                scale=self.scale,
                minimum_mark=Decimal(minimum),
                maximum_mark=Decimal(maximum),
                letter_grade=letter,
                grade_point=Decimal(points),
                remark=remark,
                is_pass=is_pass,
            )

    def save_lecturer_marks(self):
        self.client.force_login(self.lecturer)
        response = self.client.post(
            reverse(
                "academics:lecturer_result_sheet",
                args=[self.lecturer_assignment.pk],
            ),
            {
                "grades-TOTAL_FORMS": "1",
                "grades-INITIAL_FORMS": "1",
                "grades-MIN_NUM_FORMS": "0",
                "grades-MAX_NUM_FORMS": "1000",
                "grades-0-registration_id": str(self.registration.pk),
                "grades-0-coursework_mark": "28.00",
                "grades-0-examination_mark": "42.00",
                "save_marks": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        return LecturerResultSheet.objects.get(
            lecturer_assignment=self.lecturer_assignment
        )

    def submit_lecturer_sheet(self):
        sheet = self.save_lecturer_marks()
        response = self.client.post(
            reverse(
                "academics:submit_lecturer_result_sheet",
                args=[sheet.pk],
            ),
            {"submit-confirmation": "on"},
        )
        self.assertEqual(response.status_code, 302)
        sheet.refresh_from_db()
        return sheet

    def test_student_cannot_open_lecturer_dashboard(self):
        self.client.force_login(self.student_user)
        response = self.client.get(
            reverse("academics:lecturer_result_dashboard")
        )
        self.assertEqual(response.status_code, 403)

    def test_lecturer_account_dashboard_redirects_to_result_dashboard(self):
        self.client.force_login(self.lecturer)

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(
            response,
            reverse("academics:lecturer_result_dashboard"),
            fetch_redirect_response=False,
        )

    def test_lecturer_saves_marks_with_calculated_grade_and_audit(self):
        sheet = self.save_lecturer_marks()
        grade = StudentGrade.objects.get(registration=self.registration)

        self.assertEqual(grade.entered_by, self.lecturer)
        self.assertEqual(grade.lecturer_result_sheet, sheet)
        self.assertEqual(grade.total_mark, Decimal("70.00"))
        self.assertEqual(grade.letter_grade, "A")
        self.assertTrue(
            LecturerResultSheetAuditLog.objects.filter(
                sheet=sheet,
                action="marks_saved",
                actor=self.lecturer,
            ).exists()
        )

    def test_lecturer_submission_notifies_hod(self):
        sheet = self.submit_lecturer_sheet()

        self.assertEqual(sheet.status, "submitted")
        self.assertIsNotNone(sheet.submitted_at)
        self.assertTrue(
            Notification.objects.filter(
                user=self.hod,
                message__icontains="CSC210",
            ).exists()
        )

    def test_hod_approval_unlocks_existing_dean_submission_workflow(self):
        sheet = self.submit_lecturer_sheet()
        submission = SemesterResultSubmission.objects.get(
            assignment=self.student_assignment,
            semester=self.semester,
        )

        self.client.force_login(self.hod)
        blocked_response = self.client.post(
            reverse(
                "academics:submit_results_to_dean",
                args=[submission.pk],
            ),
            {"submit-confirmation": "on"},
        )
        self.assertEqual(blocked_response.status_code, 302)
        submission.refresh_from_db()
        self.assertEqual(submission.status, "draft")

        review_response = self.client.post(
            reverse(
                "academics:hod_review_lecturer_sheet",
                args=[sheet.pk],
            ),
            {"action": "approve", "review_notes": "Marks verified."},
        )
        self.assertEqual(review_response.status_code, 302)
        sheet.refresh_from_db()
        self.assertEqual(sheet.status, "approved")

        submit_response = self.client.post(
            reverse(
                "academics:submit_results_to_dean",
                args=[submission.pk],
            ),
            {"submit-confirmation": "on"},
        )
        self.assertEqual(submit_response.status_code, 302)
        submission.refresh_from_db()
        self.assertEqual(submission.status, "submitted")

    def test_hod_return_requires_reason_and_notifies_lecturer(self):
        sheet = self.submit_lecturer_sheet()
        self.client.force_login(self.hod)

        invalid_response = self.client.post(
            reverse(
                "academics:hod_review_lecturer_sheet",
                args=[sheet.pk],
            ),
            {"action": "return", "review_notes": ""},
        )
        self.assertEqual(invalid_response.status_code, 200)
        sheet.refresh_from_db()
        self.assertEqual(sheet.status, "submitted")

        response = self.client.post(
            reverse(
                "academics:hod_review_lecturer_sheet",
                args=[sheet.pk],
            ),
            {"action": "return", "review_notes": "Recheck the CAT mark."},
        )
        self.assertEqual(response.status_code, 302)
        sheet.refresh_from_db()
        self.assertEqual(sheet.status, "returned")
        self.assertTrue(
            Notification.objects.filter(
                user=self.lecturer,
                message__icontains="returned",
            ).exists()
        )
