from django.urls import path

from . import payment_views
from . import views


app_name = "payments"


urlpatterns = [
    path(
        "",
        views.placement_assistance_home,
        name="placement_assistance",
    ),
    path(
        "verification/submit/",
        views.submit_verification,
        name="submit_verification",
    ),
    path(
        "preferences/",
        views.placement_preferences,
        name="placement_preferences",
    ),
    path(
        "payment/initiate/",
        payment_views.initiate_payment,
        name="initiate_payment",
    ),
    path(
        "mpesa/callback/",
        payment_views.mpesa_callback,
        name="mpesa_callback",
    ),
    path(
        "institution/verifications/",
        views.institution_verifications,
        name="institution_verifications",
    ),
    path(
        "institution/verifications/<int:verification_id>/review/",
        views.review_verification,
        name="review_verification",
    ),
    path(
        "institution/paid-requests/",
        views.institution_paid_requests,
        name="institution_paid_requests",
    ),
    path(
        "institution/paid-requests/<int:request_id>/",
        views.institution_paid_request_detail,
        name="institution_paid_request_detail",
    ),
    path(
        "institution/paid-requests/<int:request_id>/update/",
        views.update_paid_request,
        name="update_paid_request",
    ),
]
