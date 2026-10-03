from django.contrib import admin

from .models import (
    PaymentAuditEvent,
    PaymentTransaction,
    PlacementAssistanceRequest,
    StudentVerification,
)


@admin.register(StudentVerification)
class StudentVerificationAdmin(admin.ModelAdmin):

    list_display = (
        "student_name",
        "institution_name",
        "admission_number",
        "verification_method",
        "status",
        "verified_by",
        "verified_at",
        "submitted_at",
    )

    list_filter = (
        "status",
        "verification_method",
        "assignment__institution",
        "submitted_at",
    )

    search_fields = (
        "assignment__student__full_name",
        "assignment__student__user__username",
        "assignment__student__user__email",
        "assignment__admission_number",
        "assignment__institution__institution_name",
    )

    readonly_fields = (
        "submitted_at",
        "verified_at",
        "updated_at",
        "document_deleted_at",
    )

    autocomplete_fields = (
        "assignment",
        "verified_by",
    )

    ordering = (
        "-submitted_at",
    )

    @admin.display(
        description="Student",
        ordering="assignment__student__full_name",
    )
    def student_name(self, obj):
        return (
            obj.student.full_name
            or obj.student.user.get_full_name()
            or obj.student.user.username
        )

    @admin.display(
        description="Institution",
        ordering="assignment__institution__institution_name",
    )
    def institution_name(self, obj):
        return obj.institution.institution_name

    @admin.display(
        description="Admission number",
        ordering="assignment__admission_number",
    )
    def admission_number(self, obj):
        return obj.assignment.admission_number


@admin.register(PlacementAssistanceRequest)
class PlacementAssistanceRequestAdmin(admin.ModelAdmin):

    list_display = (
        "student_name",
        "institution_name",
        "attachment_field",
        "placement_mode",
        "status",
        "payment_status",
        "expected_start_date",
        "created_at",
    )

    list_filter = (
        "status",
        "placement_mode",
        "assignment__institution",
        "expected_start_date",
        "created_at",
    )

    search_fields = (
        "assignment__student__full_name",
        "assignment__student__user__username",
        "assignment__student__user__email",
        "assignment__admission_number",
        "attachment_field",
        "preferred_counties",
    )

    readonly_fields = (
        "terms_accepted_at",
        "activated_at",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "assignment",
        "verification",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(
        description="Student",
        ordering="assignment__student__full_name",
    )
    def student_name(self, obj):
        return (
            obj.student.full_name
            or obj.student.user.get_full_name()
            or obj.student.user.username
        )

    @admin.display(
        description="Institution",
        ordering="assignment__institution__institution_name",
    )
    def institution_name(self, obj):
        return obj.institution.institution_name

    @admin.display(
        description="Payment",
        boolean=True,
    )
    def payment_status(self, obj):
        return obj.is_paid


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "student_name",
        "institution_name",
        "amount",
        "currency",
        "masked_phone",
        "provider",
        "status",
        "mpesa_receipt_number",
        "initiated_at",
        "paid_at",
    )

    list_filter = (
        "status",
        "provider",
        "currency",
        "initiated_at",
        "paid_at",
    )

    search_fields = (
        "placement_request__assignment__student__full_name",
        (
            "placement_request__assignment__student__"
            "user__username"
        ),
        (
            "placement_request__assignment__student__"
            "user__email"
        ),
        "phone_number",
        "merchant_request_id",
        "checkout_request_id",
        "mpesa_receipt_number",
    )

    readonly_fields = (
        "idempotency_key",
        "merchant_request_id",
        "checkout_request_id",
        "mpesa_receipt_number",
        "result_code",
        "result_description",
        "callback_payload",
        "initiated_at",
        "paid_at",
        "updated_at",
    )

    autocomplete_fields = (
        "placement_request",
    )

    ordering = (
        "-initiated_at",
    )

    @admin.display(
        description="Student",
    )
    def student_name(self, obj):
        return (
            obj.student.full_name
            or obj.student.user.get_full_name()
            or obj.student.user.username
        )

    @admin.display(
        description="Institution",
    )
    def institution_name(self, obj):
        return obj.institution.institution_name

    @admin.display(
        description="Phone",
    )
    def masked_phone(self, obj):
        return obj.masked_phone_number


@admin.register(PaymentAuditEvent)
class PaymentAuditEventAdmin(admin.ModelAdmin):

    list_display = (
        "transaction",
        "event_type",
        "actor",
        "created_at",
    )

    list_filter = (
        "event_type",
        "created_at",
    )

    search_fields = (
        "transaction__mpesa_receipt_number",
        "transaction__checkout_request_id",
        "transaction__merchant_request_id",
        "message",
    )

    readonly_fields = (
        "transaction",
        "event_type",
        "message",
        "payload",
        "actor",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False