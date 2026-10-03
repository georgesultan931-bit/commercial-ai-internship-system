from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from academics.models import (
    Department,
    Programme,
    SchoolFaculty,
    StudentAcademicAssignment,
)
from institutions.models import InstitutionProfile
from students.models import StudentProfile

from .models import (
    PLACEMENT_ASSISTANCE_FEE,
    PaymentTransaction,
    PlacementAssistanceRequest,
    StudentVerification,
)


class PaymentModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.institution_user = User.objects.create_user(
            username="payment-institution",
            email="payment-institution@example.com",
            password="StrongPass123!",
            role="institution",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        cls.reviewer = User.objects.create_user(
            username="payment-reviewer",
            email="payment-reviewer@example.com",
            password="StrongPass123!",
            role="institution",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        cls.student_user = User.objects.create_user(
            username="payment-student",
            email="payment-student@example.com",
            password="StrongPass123!",
            role="student",
            is_active=True,
            is_approved=True,
            is_email_verified=True,
        )

        cls.institution = InstitutionProfile.objects.create(
            user=cls.institution_user,
            institution_name="Payment Test University",
            institution_type="university",
            registration_number="PTU-001",
            official_email="registry@ptu.example.com",
            is_verified=True,
        )

        cls.school = SchoolFaculty.objects.create(
            institution=cls.institution,
            name="School of Computing",
            code="SOC",
            is_active=True,
        )

        cls.department = Department.objects.create(
            school=cls.school,
            name="Department of Computer Science",
            code="CS",
            is_active=True,
        )

        cls.programme = Programme.objects.create(
            department=cls.department,
            name="Diploma in Computer Science",
            code="DCS",
            qualification_level="Diploma",
            duration_years=3,
            is_active=True,
        )

        cls.student = StudentProfile.objects.create(
            user=cls.student_user,
            first_name="Payment",
            surname="Student",
            full_name="Payment Student",
            course="Diploma in Computer Science",
            institution_profile=cls.institution,
            phone_number="0712345678",
        )

        cls.assignment = StudentAcademicAssignment.objects.create(
            student=cls.student,
            institution=cls.institution,
            school=cls.school,
            department=cls.department,
            programme=cls.programme,
            admission_number="PTU/DCS/001",
            year_of_study=2,
            is_active=True,
        )

    def create_verified_verification(self):
        return StudentVerification.objects.create(
            assignment=self.assignment,
            verification_method="academic_record",
            status="verified",
            verified_by=self.reviewer,
            institution_notes=(
                "Verified against the institution register."
            ),
        )

    def create_placement_request(
        self,
        verification=None,
    ):
        if verification is None:
            verification = (
                self.create_verified_verification()
            )

        return PlacementAssistanceRequest.objects.create(
            assignment=self.assignment,
            verification=verification,
            preferred_counties=(
                "Kisumu, Nakuru, Nairobi"
            ),
            attachment_field=(
                "Software Development"
            ),
            placement_mode="hybrid",
            expected_start_date=(
                date.today()
                + timedelta(days=30)
            ),
            duration_weeks=12,
            additional_requirements=(
                "Prefer an organization with an ICT team."
            ),
            terms_accepted=True,
            status="awaiting_payment",
        )

    def create_payment(
        self,
        placement_request=None,
        **overrides,
    ):
        if placement_request is None:
            placement_request = (
                self.create_placement_request()
            )

        values = {
            "placement_request": placement_request,
            "provider": "mpesa_sandbox",
            "amount": PLACEMENT_ASSISTANCE_FEE,
            "phone_number": "254712345678",
            "status": "initiated",
        }

        values.update(overrides)

        return PaymentTransaction.objects.create(
            **values
        )

    def test_verified_student_records_verification_time(self):
        verification = (
            self.create_verified_verification()
        )

        self.assertEqual(
            verification.status,
            "verified",
        )

        self.assertIsNotNone(
            verification.verified_at,
        )

        self.assertEqual(
            verification.student,
            self.student,
        )

        self.assertEqual(
            verification.institution,
            self.institution,
        )

    def test_verification_requires_verified_by_user(self):
        verification = StudentVerification(
            assignment=self.assignment,
            verification_method="academic_record",
            status="verified",
        )

        with self.assertRaises(ValidationError):
            verification.save()

    def test_unverified_institution_cannot_verify_student(self):
        self.institution.is_verified = False
        self.institution.save(
            update_fields=[
                "is_verified",
            ]
        )

        verification = StudentVerification(
            assignment=self.assignment,
            verification_method="academic_record",
            status="pending",
        )

        with self.assertRaises(ValidationError):
            verification.save()

    def test_payment_amount_is_fixed_at_1500(self):
        payment = self.create_payment()

        self.assertEqual(
            payment.amount,
            Decimal("1500.00"),
        )

        self.assertEqual(
            payment.currency,
            "KES",
        )

    def test_different_payment_amount_is_rejected(self):
        placement_request = (
            self.create_placement_request()
        )

        payment = PaymentTransaction(
            placement_request=placement_request,
            provider="mpesa_sandbox",
            amount=Decimal("1000.00"),
            phone_number="254712345678",
            status="initiated",
        )

        with self.assertRaises(ValidationError):
            payment.save()

    def test_local_phone_format_is_rejected(self):
        placement_request = (
            self.create_placement_request()
        )

        payment = PaymentTransaction(
            placement_request=placement_request,
            provider="mpesa_sandbox",
            amount=PLACEMENT_ASSISTANCE_FEE,
            phone_number="0712345678",
            status="initiated",
        )

        with self.assertRaises(ValidationError):
            payment.save()

    def test_successful_payment_requires_receipt(self):
        placement_request = (
            self.create_placement_request()
        )

        payment = PaymentTransaction(
            placement_request=placement_request,
            provider="mpesa_sandbox",
            amount=PLACEMENT_ASSISTANCE_FEE,
            phone_number="254712345678",
            status="successful",
        )

        with self.assertRaises(ValidationError):
            payment.save()

    def test_successful_payment_records_paid_time(self):
        payment = self.create_payment(
            status="successful",
            mpesa_receipt_number="TEST123456",
            result_code="0",
            result_description=(
                "The service request was processed "
                "successfully."
            ),
        )

        self.assertIsNotNone(
            payment.paid_at,
        )

        self.assertEqual(
            payment.mpesa_receipt_number,
            "TEST123456",
        )

        self.assertTrue(
            payment.placement_request.is_paid
        )

    def test_unverified_student_cannot_initiate_payment(self):
        verification = StudentVerification.objects.create(
            assignment=self.assignment,
            verification_method="academic_record",
            status="pending",
        )

        placement_request = (
            PlacementAssistanceRequest.objects.create(
                assignment=self.assignment,
                verification=verification,
                preferred_counties="Kisumu",
                attachment_field="ICT Support",
                placement_mode="physical",
                expected_start_date=(
                    date.today()
                    + timedelta(days=30)
                ),
                duration_weeks=12,
                terms_accepted=True,
                status="draft",
            )
        )

        payment = PaymentTransaction(
            placement_request=placement_request,
            provider="mpesa_sandbox",
            amount=PLACEMENT_ASSISTANCE_FEE,
            phone_number="254712345678",
            status="initiated",
        )

        with self.assertRaises(ValidationError):
            payment.save()

    def test_failed_payment_cannot_activate_request(self):
        placement_request = (
            self.create_placement_request()
        )

        self.create_payment(
            placement_request=placement_request,
            status="failed",
            result_code="1",
            result_description="Payment failed.",
        )

        placement_request.status = "active"

        with self.assertRaises(ValidationError):
            placement_request.save()

    def test_successful_payment_can_activate_request(self):
        placement_request = (
            self.create_placement_request()
        )

        self.create_payment(
            placement_request=placement_request,
            status="successful",
            mpesa_receipt_number="TEST654321",
            result_code="0",
            result_description=(
                "Payment completed successfully."
            ),
        )

        placement_request.status = "active"
        placement_request.save()

        self.assertEqual(
            placement_request.status,
            "active",
        )

        self.assertIsNotNone(
            placement_request.activated_at,
        )

    def test_phone_number_is_masked_for_display(self):
        payment = self.create_payment()

        self.assertEqual(
            payment.masked_phone_number,
            "25471***678",
        )