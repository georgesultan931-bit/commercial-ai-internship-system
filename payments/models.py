import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone


PLACEMENT_ASSISTANCE_FEE = Decimal("1500.00")


kenyan_phone_validator = RegexValidator(
    regex=r"^254(?:7|1)\d{8}$",
    message=(
        "Enter the phone number in Kenyan international "
        "format, for example 254712345678."
    ),
)


class StudentVerification(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending Verification"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    )

    METHOD_CHOICES = (
        (
            "academic_record",
            "Institution Academic Record",
        ),
        (
            "student_id",
            "Student ID Document",
        ),
        (
            "manual",
            "Manual Institution Review",
        ),
    )

    assignment = models.OneToOneField(
        "academics.StudentAcademicAssignment",
        on_delete=models.CASCADE,
        related_name="placement_verification",
    )

    verification_method = models.CharField(
        max_length=30,
        choices=METHOD_CHOICES,
        default="academic_record",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )

    student_id_document = models.ImageField(
        upload_to="student_verification_ids/%Y/%m/",
        blank=True,
        null=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="student_verifications_completed",
        blank=True,
        null=True,
    )

    rejection_reason = models.TextField(
        blank=True,
        default="",
    )

    institution_notes = models.TextField(
        blank=True,
        default="",
    )

    document_deleted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-submitted_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "status",
                    "submitted_at",
                ],
                name="payment_verify_status_idx",
            ),
        ]

    @property
    def student(self):
        return self.assignment.student

    @property
    def institution(self):
        return self.assignment.institution

    def clean(self):
        errors = {}

        if self.assignment_id:
            if not self.assignment.is_active:
                errors["assignment"] = (
                    "The student's academic assignment is inactive."
                )

            if not self.assignment.institution.is_verified:
                errors["assignment"] = (
                    "The institution must be verified before "
                    "the student can be approved."
                )

        if (
            self.verification_method == "student_id"
            and not self.student_id_document
        ):
            errors["student_id_document"] = (
                "Upload the student ID document when using "
                "student ID verification."
            )

        if (
            self.status == "verified"
            and not self.verified_by_id
        ):
            errors["verified_by"] = (
                "Record the institution staff member who "
                "verified the student."
            )

        if (
            self.status == "rejected"
            and not self.rejection_reason.strip()
        ):
            errors["rejection_reason"] = (
                "Provide a reason when rejecting verification."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.status == "verified":
            if self.verified_at is None:
                self.verified_at = timezone.now()
        else:
            self.verified_at = None

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.assignment.student} - "
            f"{self.get_status_display()}"
        )


class PlacementAssistanceRequest(models.Model):

    PLACEMENT_MODE_CHOICES = (
        ("any", "Any Placement Mode"),
        ("physical", "Physical"),
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
    )

    STATUS_CHOICES = (
        ("draft", "Draft"),
        (
            "awaiting_verification",
            "Awaiting Verification",
        ),
        (
            "awaiting_payment",
            "Awaiting Payment",
        ),
        ("active", "Active"),
        ("matching", "Matching in Progress"),
        ("shortlisted", "Opportunity Shortlisted"),
        ("placed", "Placement Found"),
        ("cancelled", "Cancelled"),
    )

    assignment = models.OneToOneField(
        "academics.StudentAcademicAssignment",
        on_delete=models.CASCADE,
        related_name="placement_assistance_request",
    )

    verification = models.OneToOneField(
        StudentVerification,
        on_delete=models.PROTECT,
        related_name="placement_request",
    )

    preferred_counties = models.TextField(
        help_text=(
            "Comma-separated preferred counties, "
            "for example Kisumu, Nakuru, Nairobi."
        ),
    )

    attachment_field = models.CharField(
        max_length=200,
        help_text=(
            "The student's preferred attachment field."
        ),
    )

    placement_mode = models.CharField(
        max_length=20,
        choices=PLACEMENT_MODE_CHOICES,
        default="any",
    )

    expected_start_date = models.DateField()

    duration_weeks = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(52),
        ],
    )

    additional_requirements = models.TextField(
        blank=True,
        default="",
    )

    terms_accepted = models.BooleanField(
        default=False,
    )

    terms_accepted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )

    matched_opportunity = models.ForeignKey(
        "internships.InternshipOpportunity",
        on_delete=models.SET_NULL,
        related_name="placement_assistance_matches",
        blank=True,
        null=True,
    )

    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="placement_assistance_requests_managed",
        blank=True,
        null=True,
    )

    institution_notes = models.TextField(
        blank=True,
        default="",
    )

    activated_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    matching_started_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    shortlisted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    placed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "status",
                    "created_at",
                ],
                name="payment_request_status_idx",
            ),
        ]

    @property
    def student(self):
        return self.assignment.student

    @property
    def institution(self):
        return self.assignment.institution

    @property
    def successful_payment(self):
        return self.payment_transactions.filter(
            status="successful",
        ).first()

    @property
    def is_paid(self):
        return self.payment_transactions.filter(
            status="successful",
        ).exists()

    def clean(self):
        errors = {}

        if (
            self.assignment_id
            and self.verification_id
        ):
            if (
                self.verification.assignment_id
                != self.assignment_id
            ):
                errors["verification"] = (
                    "The verification record does not belong "
                    "to this academic assignment."
                )

        if (
            self.status
            in {
                "awaiting_payment",
                "active",
                "matching",
                "shortlisted",
                "placed",
            }
            and self.verification_id
            and self.verification.status != "verified"
        ):
            errors["status"] = (
                "The student must be verified before "
                "entering this stage."
            )

        if self.status in {
            "active",
            "matching",
            "shortlisted",
            "placed",
        }:
            has_successful_payment = (
                self.pk
                and self.payment_transactions.filter(
                    status="successful",
                ).exists()
            )

            if not has_successful_payment:
                errors["status"] = (
                    "A successful verified payment is required "
                    "before placement assistance can be activated."
                )

        if (
            self.status
            in {
                "shortlisted",
                "placed",
            }
            and not self.matched_opportunity_id
        ):
            errors["matched_opportunity"] = (
                "Select an internship opportunity before "
                "shortlisting or placing the student."
            )

        if (
            self.status
            in {
                "awaiting_payment",
                "active",
                "matching",
                "shortlisted",
                "placed",
            }
            and not self.terms_accepted
        ):
            errors["terms_accepted"] = (
                "The student must accept the placement "
                "assistance terms."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.terms_accepted:
            if self.terms_accepted_at is None:
                self.terms_accepted_at = timezone.now()
        else:
            self.terms_accepted_at = None

        if self.status == "active":
            if self.activated_at is None:
                self.activated_at = timezone.now()

        if self.status == "matching":
            if self.activated_at is None:
                self.activated_at = timezone.now()
            if self.matching_started_at is None:
                self.matching_started_at = timezone.now()

        if self.status == "shortlisted":
            if self.activated_at is None:
                self.activated_at = timezone.now()
            if self.matching_started_at is None:
                self.matching_started_at = timezone.now()
            if self.shortlisted_at is None:
                self.shortlisted_at = timezone.now()

        if self.status == "placed":
            if self.activated_at is None:
                self.activated_at = timezone.now()
            if self.matching_started_at is None:
                self.matching_started_at = timezone.now()
            if self.shortlisted_at is None:
                self.shortlisted_at = timezone.now()
            if self.placed_at is None:
                self.placed_at = timezone.now()

        elif self.status in {
            "draft",
            "awaiting_verification",
            "awaiting_payment",
            "cancelled",
        }:
            self.activated_at = None
            self.matching_started_at = None
            self.shortlisted_at = None
            self.placed_at = None

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.assignment.student} - "
            f"{self.get_status_display()}"
        )


class PaymentTransaction(models.Model):

    STATUS_CHOICES = (
        ("initiated", "Initiated"),
        ("pending", "Pending Customer Response"),
        ("successful", "Successful"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled by Customer"),
        ("timed_out", "Timed Out"),
        ("refunded", "Refunded"),
    )

    PROVIDER_CHOICES = (
        ("mpesa_sandbox", "M-Pesa Sandbox"),
        ("mpesa", "M-Pesa"),
    )

    placement_request = models.ForeignKey(
        PlacementAssistanceRequest,
        on_delete=models.PROTECT,
        related_name="payment_transactions",
    )

    idempotency_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    provider = models.CharField(
        max_length=30,
        choices=PROVIDER_CHOICES,
        default="mpesa_sandbox",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=PLACEMENT_ASSISTANCE_FEE,
        validators=[
            MinValueValidator(
                PLACEMENT_ASSISTANCE_FEE
            ),
        ],
    )

    currency = models.CharField(
        max_length=3,
        default="KES",
        editable=False,
    )

    phone_number = models.CharField(
        max_length=15,
        validators=[
            kenyan_phone_validator,
        ],
        help_text=(
            "Use Kenyan international format, "
            "for example 254712345678."
        ),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="initiated",
        db_index=True,
    )

    merchant_request_id = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        unique=True,
    )

    checkout_request_id = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        unique=True,
    )

    mpesa_receipt_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
    )

    result_code = models.CharField(
        max_length=30,
        blank=True,
        default="",
    )

    result_description = models.TextField(
        blank=True,
        default="",
    )

    callback_payload = models.JSONField(
        blank=True,
        default=dict,
    )

    initiated_at = models.DateTimeField(
        auto_now_add=True,
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-initiated_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "status",
                    "initiated_at",
                ],
                name="payment_tx_status_idx",
            ),
            models.Index(
                fields=[
                    "phone_number",
                    "initiated_at",
                ],
                name="payment_tx_phone_idx",
            ),
        ]

    @property
    def student(self):
        return self.placement_request.student

    @property
    def institution(self):
        return self.placement_request.institution

    @property
    def masked_phone_number(self):
        if len(self.phone_number) < 7:
            return self.phone_number

        return (
            f"{self.phone_number[:5]}"
            f"***"
            f"{self.phone_number[-3:]}"
        )

    def clean(self):
        errors = {}

        if self.amount != PLACEMENT_ASSISTANCE_FEE:
            errors["amount"] = (
                "The placement assistance fee must be "
                "KES 1,500.00."
            )

        if self.currency != "KES":
            errors["currency"] = (
                "Placement assistance payments must use KES."
            )

        if self.placement_request_id:
            request = self.placement_request

            if request.verification.status != "verified":
                errors["placement_request"] = (
                    "Payment cannot be initiated before "
                    "student verification."
                )

            if not request.terms_accepted:
                errors["placement_request"] = (
                    "Payment cannot be initiated before the "
                    "student accepts the service terms."
                )

        if (
            self.status == "successful"
            and not self.mpesa_receipt_number
        ):
            errors["mpesa_receipt_number"] = (
                "A successful payment must have an "
                "M-Pesa receipt number."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.status == "successful":
            if self.paid_at is None:
                self.paid_at = timezone.now()
        elif self.status not in {
            "refunded",
        }:
            self.paid_at = None

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.student} - "
            f"KES {self.amount} - "
            f"{self.get_status_display()}"
        )


class PaymentAuditEvent(models.Model):

    EVENT_TYPE_CHOICES = (
        ("created", "Payment Created"),
        ("stk_requested", "STK Push Requested"),
        ("stk_accepted", "STK Request Accepted"),
        ("callback_received", "Callback Received"),
        ("status_changed", "Status Changed"),
        ("query_performed", "Status Query Performed"),
        ("refund_requested", "Refund Requested"),
        ("refunded", "Refunded"),
        ("error", "Error"),
    )

    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name="audit_events",
    )

    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPE_CHOICES,
    )

    message = models.TextField(
        blank=True,
        default="",
    )

    payload = models.JSONField(
        blank=True,
        default=dict,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="payment_audit_events",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "event_type",
                    "created_at",
                ],
                name="payment_audit_event_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.transaction_id} - "
            f"{self.get_event_type_display()}"
        )
