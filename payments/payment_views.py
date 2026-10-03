from datetime import timedelta
import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from notifications.models import Notification

from .forms import PaymentInitiationForm
from .models import (
    PLACEMENT_ASSISTANCE_FEE,
    PaymentAuditEvent,
    PaymentTransaction,
    PlacementAssistanceRequest,
)
from .mpesa import (
    MpesaConfigurationError,
    MpesaRequestError,
    initiate_stk_push,
)


def _callback_response():
    return JsonResponse(
        {
            "ResultCode": 0,
            "ResultDesc": "Callback accepted",
        }
    )


def _callback_metadata(callback):
    metadata = (
        callback
        .get("CallbackMetadata", {})
        .get("Item", [])
    )

    values = {}

    for item in metadata:
        name = item.get("Name")

        if name:
            values[name] = item.get("Value")

    return values


def _failure_status(result_code):
    result_code = str(result_code)

    if result_code == "1032":
        return "cancelled"

    if result_code == "1037":
        return "timed_out"

    return "failed"


@login_required
def initiate_payment(request):
    if request.user.role != "student":
        messages.error(
            request,
            "Only student accounts can initiate payment.",
        )

        return redirect("dashboard")

    if request.method != "POST":
        return redirect(
            "payments:placement_assistance"
        )

    placement_request_id = request.POST.get(
        "placement_request_id"
    )

    try:
        placement_request_id = int(
            placement_request_id
        )
    except (TypeError, ValueError):
        messages.error(
            request,
            "Invalid placement assistance request.",
        )

        return redirect(
            "payments:placement_assistance"
        )

    form = PaymentInitiationForm(
        request.POST
    )

    if not form.is_valid():
        error_message = " ".join(
            error
            for errors in form.errors.values()
            for error in errors
        )

        messages.error(
            request,
            error_message,
        )

        return redirect(
            "payments:placement_assistance"
        )

    phone_number = form.cleaned_data[
        "phone_number"
    ]

    with transaction.atomic():
        placement_request = get_locked_request(
            placement_request_id,
            request.user,
        )

        if placement_request is None:
            messages.error(
                request,
                (
                    "The placement assistance request "
                    "was not found."
                ),
            )

            return redirect(
                "payments:placement_assistance"
            )

        if placement_request.is_paid:
            messages.info(
                request,
                "This placement request is already paid.",
            )

            return redirect(
                "payments:placement_assistance"
            )

        if (
            placement_request.verification.status
            != "verified"
        ):
            messages.error(
                request,
                (
                    "Your institution must verify you "
                    "before payment."
                ),
            )

            return redirect(
                "payments:placement_assistance"
            )

        if not placement_request.terms_accepted:
            messages.error(
                request,
                (
                    "Accept the placement assistance "
                    "terms before payment."
                ),
            )

            return redirect(
                "payments:placement_assistance"
            )

        if (
            placement_request.status
            != "awaiting_payment"
        ):
            messages.error(
                request,
                (
                    "This placement request is not ready "
                    "for payment."
                ),
            )

            return redirect(
                "payments:placement_assistance"
            )

        # These timers solve two different problems and must not
        # be combined. The short duplicate guard prevents a rapid
        # double-click. The longer pending timeout gives M-Pesa
        # enough time to deliver its asynchronous callback.
        duplicate_guard_seconds = int(
            getattr(
                settings,
                "MPESA_DUPLICATE_GUARD_SECONDS",
                5,
            )
        )

        pending_timeout_seconds = int(
            getattr(
                settings,
                "MPESA_PENDING_TIMEOUT_SECONDS",
                180,
            )
        )

        duplicate_guard_seconds = max(
            1,
            duplicate_guard_seconds,
        )
        pending_timeout_seconds = max(
            60,
            pending_timeout_seconds,
        )

        now = timezone.now()
        pending_cutoff = (
            now
            - timedelta(
                seconds=pending_timeout_seconds
            )
        )

        open_transactions = (
            placement_request
            .payment_transactions
            .filter(
                status__in=[
                    "initiated",
                    "pending",
                ],
            )
        )

        stale_transactions = list(
            open_transactions.filter(
                initiated_at__lte=pending_cutoff,
            )
        )

        for stale_payment in stale_transactions:
            old_status = stale_payment.status

            stale_payment.status = "timed_out"
            stale_payment.result_description = (
                "The previous M-Pesa prompt expired "
                "before payment was confirmed."
            )

            stale_payment.save(
                update_fields=[
                    "status",
                    "result_description",
                    "paid_at",
                    "updated_at",
                ]
            )

            PaymentAuditEvent.objects.create(
                transaction=stale_payment,
                event_type="status_changed",
                message=(
                    f"Payment changed from {old_status} "
                    "to timed_out before a retry."
                ),
                actor=request.user,
                payload={
                    "pending_timeout_seconds": (
                        pending_timeout_seconds
                    ),
                },
            )

        pending_transaction = (
            open_transactions
            .filter(
                initiated_at__gt=pending_cutoff,
            )
            .first()
        )

        if pending_transaction is not None:
            elapsed_seconds = max(
                0,
                int(
                    (
                        now
                        - pending_transaction.initiated_at
                    ).total_seconds()
                ),
            )
            remaining_seconds = max(
                1,
                pending_timeout_seconds
                - elapsed_seconds,
            )
            remaining_minutes = max(
                1,
                (
                    remaining_seconds + 59
                ) // 60,
            )

            pending_message = (
                "An M-Pesa payment is still awaiting a final "
                "response for "
                f"{pending_transaction.masked_phone_number}. "
                "To prevent duplicate charges, do not send "
                "another prompt yet. Wait up to "
                f"{remaining_minutes} minute"
                f"{'s' if remaining_minutes != 1 else ''}, "
                "then try again only if no payment was deducted."
            )

            messages.info(
                request,
                pending_message,
            )

            return redirect(
                "payments:placement_assistance"
            )

        duplicate_cutoff = (
            now
            - timedelta(
                seconds=duplicate_guard_seconds
            )
        )

        recently_created_transaction = (
            placement_request
            .payment_transactions
            .filter(
                initiated_at__gt=duplicate_cutoff,
            )
            .first()
        )

        if recently_created_transaction is not None:
            messages.info(
                request,
                (
                    "Please wait a few seconds before "
                    "submitting another M-Pesa request."
                ),
            )

            return redirect(
                "payments:placement_assistance"
            )

        provider = (
            "mpesa"
            if settings.MPESA_ENVIRONMENT
            == "production"
            else "mpesa_sandbox"
        )

        payment = PaymentTransaction.objects.create(
            placement_request=placement_request,
            provider=provider,
            amount=PLACEMENT_ASSISTANCE_FEE,
            phone_number=phone_number,
            status="initiated",
        )

        PaymentAuditEvent.objects.create(
            transaction=payment,
            event_type="created",
            message=(
                "Payment transaction created by student."
            ),
            actor=request.user,
            payload={
                "amount": str(
                    PLACEMENT_ASSISTANCE_FEE
                ),
                "currency": "KES",
                "provider": provider,
            },
        )

        PaymentAuditEvent.objects.create(
            transaction=payment,
            event_type="stk_requested",
            message=(
                "STK Push request prepared for M-Pesa."
            ),
            actor=request.user,
            payload={
                "phone_number": (
                    payment.masked_phone_number
                ),
            },
        )

    try:
        response = initiate_stk_push(
            phone_number=phone_number,
            amount=PLACEMENT_ASSISTANCE_FEE,
            account_reference=(
                f"PLACEMENT{placement_request.id}"
            ),
            transaction_description=(
                "Placement assistance"
            ),
        )

    except (
        MpesaConfigurationError,
        MpesaRequestError,
    ) as error:
        with transaction.atomic():
            payment = (
                PaymentTransaction.objects
                .select_for_update()
                .get(
                    id=payment.id,
                )
            )

            payment.status = "failed"
            payment.result_description = str(error)
            payment.save(
                update_fields=[
                    "status",
                    "result_description",
                    "paid_at",
                    "updated_at",
                ]
            )

            PaymentAuditEvent.objects.create(
                transaction=payment,
                event_type="error",
                message=(
                    "STK Push request failed."
                ),
                actor=request.user,
                payload={
                    "error": str(error),
                },
            )

        messages.error(
            request,
            (
                "The M-Pesa prompt could not be sent. "
                f"{error}"
            ),
        )

        return redirect(
            "payments:placement_assistance"
        )

    with transaction.atomic():
        payment = (
            PaymentTransaction.objects
            .select_for_update()
            .get(
                id=payment.id,
            )
        )

        payment.status = "pending"
        payment.merchant_request_id = response[
            "merchant_request_id"
        ]
        payment.checkout_request_id = response[
            "checkout_request_id"
        ]
        payment.result_code = response[
            "response_code"
        ]
        payment.result_description = (
            response["customer_message"]
            or response["response_description"]
        )

        payment.save(
            update_fields=[
                "status",
                "merchant_request_id",
                "checkout_request_id",
                "result_code",
                "result_description",
                "paid_at",
                "updated_at",
            ]
        )

        PaymentAuditEvent.objects.create(
            transaction=payment,
            event_type="stk_accepted",
            message=(
                "M-Pesa accepted the STK Push request."
            ),
            actor=request.user,
            payload=response["raw_response"],
        )

    messages.success(
        request,
        (
            "M-Pesa accepted the request. Check the phone "
            f"{payment.masked_phone_number} and enter the "
            "PIN only in the secure M-Pesa prompt."
        ),
    )

    return redirect(
        "payments:placement_assistance"
    )


def get_locked_request(
    placement_request_id,
    user,
):
    return (
        PlacementAssistanceRequest.objects
        .select_for_update()
        .select_related(
            "assignment",
            "assignment__student",
            "assignment__student__user",
            "assignment__institution",
            "assignment__institution__user",
            "verification",
        )
        .filter(
            id=placement_request_id,
            assignment__student__user=user,
        )
        .first()
    )


@csrf_exempt
def mpesa_callback(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "error": "POST request required.",
            },
            status=405,
        )

    try:
        payload = json.loads(
            request.body.decode("utf-8")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return JsonResponse(
            {
                "error": "Invalid JSON payload.",
            },
            status=400,
        )

    callback = (
        payload
        .get("Body", {})
        .get("stkCallback", {})
    )

    checkout_request_id = callback.get(
        "CheckoutRequestID"
    )

    merchant_request_id = callback.get(
        "MerchantRequestID"
    )

    if not (
        checkout_request_id
        or merchant_request_id
    ):
        return JsonResponse(
            {
                "error": (
                    "Missing M-Pesa transaction ID."
                ),
            },
            status=400,
        )

    with transaction.atomic():
        payment_query = (
            PaymentTransaction.objects
            .select_for_update()
            .select_related(
                "placement_request",
                "placement_request__assignment",
                "placement_request__assignment__student",
                "placement_request__assignment__student__user",
                "placement_request__assignment__institution",
                "placement_request__assignment__institution__user",
            )
        )

        payment = None

        if checkout_request_id:
            payment = payment_query.filter(
                checkout_request_id=(
                    checkout_request_id
                )
            ).first()

        if (
            payment is None
            and merchant_request_id
        ):
            payment = payment_query.filter(
                merchant_request_id=(
                    merchant_request_id
                )
            ).first()

        if payment is None:
            return _callback_response()

        PaymentAuditEvent.objects.create(
            transaction=payment,
            event_type="callback_received",
            message="M-Pesa callback received.",
            payload=payload,
        )

        if payment.status == "successful":
            return _callback_response()

        result_code = str(
            callback.get(
                "ResultCode",
                "",
            )
        )

        result_description = str(
            callback.get(
                "ResultDesc",
                "",
            )
        )

        payment.callback_payload = payload
        payment.result_code = result_code
        payment.result_description = (
            result_description
        )

        if result_code != "0":
            old_status = payment.status

            payment.status = _failure_status(
                result_code
            )

            payment.save(
                update_fields=[
                    "status",
                    "result_code",
                    "result_description",
                    "callback_payload",
                    "paid_at",
                    "updated_at",
                ]
            )

            PaymentAuditEvent.objects.create(
                transaction=payment,
                event_type="status_changed",
                message=(
                    f"Payment changed from {old_status} "
                    f"to {payment.status}."
                ),
                payload={
                    "result_code": result_code,
                    "result_description": (
                        result_description
                    ),
                },
            )

            Notification.objects.create(
                user=payment.student.user,
                message=(
                    "Your M-Pesa payment was not completed. "
                    f"{result_description}"
                ),
            )

            return _callback_response()

        metadata = _callback_metadata(
            callback
        )

        receipt_number = metadata.get(
            "MpesaReceiptNumber"
        )

        callback_amount = metadata.get(
            "Amount"
        )

        callback_phone = str(
            metadata.get(
                "PhoneNumber",
                "",
            )
        )

        try:
            callback_amount = Decimal(
                str(callback_amount)
            )
        except (
            InvalidOperation,
            TypeError,
        ):
            callback_amount = None

        validation_errors = []

        if not receipt_number:
            validation_errors.append(
                "Missing M-Pesa receipt number."
            )

        if (
            callback_amount
            != PLACEMENT_ASSISTANCE_FEE
        ):
            validation_errors.append(
                "Callback amount does not match KES 1,500."
            )

        if (
            callback_phone
            and callback_phone
            != payment.phone_number
        ):
            validation_errors.append(
                "Callback phone number does not match."
            )

        if validation_errors:
            payment.status = "failed"
            payment.result_description = " ".join(
                validation_errors
            )

            payment.save(
                update_fields=[
                    "status",
                    "result_code",
                    "result_description",
                    "callback_payload",
                    "paid_at",
                    "updated_at",
                ]
            )

            PaymentAuditEvent.objects.create(
                transaction=payment,
                event_type="error",
                message=(
                    "Successful callback failed validation."
                ),
                payload={
                    "errors": validation_errors,
                },
            )

            return _callback_response()

        payment.status = "successful"
        payment.mpesa_receipt_number = str(
            receipt_number
        )

        payment.save(
            update_fields=[
                "status",
                "mpesa_receipt_number",
                "result_code",
                "result_description",
                "callback_payload",
                "paid_at",
                "updated_at",
            ]
        )

        placement_request = (
            payment.placement_request
        )

        placement_request.status = "active"
        placement_request.save(
            update_fields=[
                "status",
                "activated_at",
                "updated_at",
            ]
        )

        PaymentAuditEvent.objects.create(
            transaction=payment,
            event_type="status_changed",
            message=(
                "Payment confirmed and placement "
                "assistance activated."
            ),
            payload={
                "receipt_number": (
                    payment.mpesa_receipt_number
                ),
                "amount": str(
                    payment.amount
                ),
            },
        )

        Notification.objects.create(
            user=payment.student.user,
            message=(
                "Your KES 1,500 placement assistance "
                "payment was successful. Receipt: "
                f"{payment.mpesa_receipt_number}. "
                "Placement matching is now active."
            ),
        )

        Notification.objects.create(
            user=payment.institution.user,
            message=(
                f"{payment.student} paid KES 1,500 for "
                "placement assistance. Matching can begin."
            ),
        )

    return _callback_response()
