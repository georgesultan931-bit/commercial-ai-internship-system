import base64
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests.auth import HTTPBasicAuth


class MpesaConfigurationError(
    ImproperlyConfigured
):
    pass


class MpesaRequestError(Exception):
    pass


def _setting(name):
    value = getattr(
        settings,
        name,
        "",
    )

    if value is None:
        return ""

    return str(value).strip()


def _required_setting(name):
    value = _setting(name)

    if not value:
        raise MpesaConfigurationError(
            f"{name} is not configured."
        )

    return value


def _base_url():
    environment = _setting(
        "MPESA_ENVIRONMENT"
    ).lower()

    if environment == "production":
        return "https://api.safaricom.co.ke"

    if environment == "sandbox":
        return "https://sandbox.safaricom.co.ke"

    raise MpesaConfigurationError(
        (
            "MPESA_ENVIRONMENT must be either "
            "'sandbox' or 'production'."
        )
    )


def _timestamp():
    return datetime.now(
        ZoneInfo("Africa/Nairobi")
    ).strftime("%Y%m%d%H%M%S")


def _password(
    shortcode,
    passkey,
    timestamp,
):
    raw_password = (
        f"{shortcode}"
        f"{passkey}"
        f"{timestamp}"
    )

    return base64.b64encode(
        raw_password.encode("utf-8")
    ).decode("utf-8")


def get_access_token():
    consumer_key = _required_setting(
        "MPESA_CONSUMER_KEY"
    )

    consumer_secret = _required_setting(
        "MPESA_CONSUMER_SECRET"
    )

    url = (
        f"{_base_url()}"
        "/oauth/v1/generate"
        "?grant_type=client_credentials"
    )

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(
                consumer_key,
                consumer_secret,
            ),
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

    except requests.RequestException as error:
        raise MpesaRequestError(
            (
                "Unable to authenticate with M-Pesa. "
                f"{error}"
            )
        ) from error

    except ValueError as error:
        raise MpesaRequestError(
            (
                "M-Pesa authentication returned an "
                "invalid response."
            )
        ) from error

    access_token = payload.get(
        "access_token"
    )

    if not access_token:
        raise MpesaRequestError(
            (
                "M-Pesa authentication did not return "
                "an access token."
            )
        )

    return access_token


def initiate_stk_push(
    *,
    phone_number,
    amount,
    account_reference,
    transaction_description,
):
    shortcode = _required_setting(
        "MPESA_SHORTCODE"
    )

    passkey = _required_setting(
        "MPESA_PASSKEY"
    )

    callback_url = _required_setting(
        "MPESA_CALLBACK_URL"
    )

    if (
        _setting("MPESA_ENVIRONMENT").lower()
        == "production"
        and not callback_url.startswith(
            "https://"
        )
    ):
        raise MpesaConfigurationError(
            (
                "MPESA_CALLBACK_URL must use HTTPS "
                "in production."
            )
        )

    decimal_amount = Decimal(
        str(amount)
    )

    if decimal_amount <= 0:
        raise MpesaRequestError(
            "The payment amount must be positive."
        )

    integer_amount = int(
        decimal_amount
    )

    timestamp = _timestamp()

    payload = {
        "BusinessShortCode": shortcode,
        "Password": _password(
            shortcode,
            passkey,
            timestamp,
        ),
        "Timestamp": timestamp,
        "TransactionType": (
            "CustomerPayBillOnline"
        ),
        "Amount": integer_amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": (
            str(account_reference)[:12]
        ),
        "TransactionDesc": (
            str(transaction_description)[:20]
        ),
    }

    access_token = get_access_token()

    url = (
        f"{_base_url()}"
        "/mpesa/stkpush/v1/processrequest"
    )

    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": (
                    f"Bearer {access_token}"
                ),
                "Content-Type": (
                    "application/json"
                ),
            },
            timeout=30,
        )

        response_payload = response.json()

    except requests.RequestException as error:
        raise MpesaRequestError(
            (
                "Unable to send the M-Pesa payment "
                f"request. {error}"
            )
        ) from error

    except ValueError as error:
        raise MpesaRequestError(
            (
                "M-Pesa returned an invalid payment "
                "response."
            )
        ) from error

    if not response.ok:
        error_message = (
            response_payload.get(
                "errorMessage"
            )
            or response_payload.get(
                "ResponseDescription"
            )
            or (
                "M-Pesa rejected the payment "
                "request."
            )
        )

        raise MpesaRequestError(
            error_message
        )

    response_code = str(
        response_payload.get(
            "ResponseCode",
            "",
        )
    )

    if response_code != "0":
        raise MpesaRequestError(
            response_payload.get(
                "ResponseDescription",
                (
                    "M-Pesa did not accept the "
                    "payment request."
                ),
            )
        )

    merchant_request_id = (
        response_payload.get(
            "MerchantRequestID"
        )
    )

    checkout_request_id = (
        response_payload.get(
            "CheckoutRequestID"
        )
    )

    if (
        not merchant_request_id
        or not checkout_request_id
    ):
        raise MpesaRequestError(
            (
                "M-Pesa accepted the request but "
                "did not return transaction IDs."
            )
        )

    return {
        "merchant_request_id": (
            merchant_request_id
        ),
        "checkout_request_id": (
            checkout_request_id
        ),
        "response_code": response_code,
        "response_description": (
            response_payload.get(
                "ResponseDescription",
                "",
            )
        ),
        "customer_message": (
            response_payload.get(
                "CustomerMessage",
                "",
            )
        ),
        "raw_response": response_payload,
    }