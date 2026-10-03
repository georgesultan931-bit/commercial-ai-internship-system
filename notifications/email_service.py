# notifications/email_service.py
import os
from types import SimpleNamespace

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags
import requests
from email.utils import parseaddr

from .models import EmailConfiguration, EmailLog


def _clean_setting(value):
    """Clean setting value"""
    if value is None:
        return ''
    return str(value).strip()


def _is_certificate_verify_error(error):
    """Check if error is certificate related"""
    return (
        'CERTIFICATE_VERIFY_FAILED' in str(error)
        or 'certificate verify failed' in str(error).lower()
    )


def _build_connection(config, allow_insecure_ssl=False):
    """Build email connection."""
    backend = None
    connection_kwargs = {}
    use_tls = bool(config.email_use_tls)

    if int(config.email_port) == 587:
        use_tls = True

    if allow_insecure_ssl:
        backend = 'notifications.email_backend.LocalSmtpEmailBackend'
        connection_kwargs['allow_insecure_ssl'] = allow_insecure_ssl

    return get_connection(
        backend=backend,
        host=config.email_host,
        port=config.email_port,
        username=config.email_host_user,
        password=config.email_host_password,
        use_tls=use_tls,
        timeout=60,
        **connection_kwargs,
    )


def _get_brevo_api_key():
    """Return the Brevo API key from Django settings or environment."""
    return _clean_setting(
        getattr(settings, "BREVO_API_KEY", "")
        or os.environ.get("BREVO_API_KEY", "")
    )

def build_html_email(title, message, button_text=None, button_url=None):
    """Build HTML email template"""
    button_html = ''

    if button_text and button_url:
        button_html = f"""
        <div style="margin-top:30px;">
            <a href="{button_url}"
               style="background:#2563eb;
                      color:white;
                      padding:14px 24px;
                      text-decoration:none;
                      border-radius:10px;
                      font-weight:700;
                      display:inline-block;">
                {button_text}
            </a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;">
        <table width="100%" style="background:#f4f7fb;padding:30px 0;">
            <tr>
                <td align="center">
                    <table width="600" style="background:white;border-radius:18px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                        <tr>
                            <td style="background:#2563eb;color:white;padding:30px;text-align:center;">
                                <h2 style="margin:0;">AI Internship & Attachment System</h2>
                                <p style="margin:10px 0 0;">Smart Recruitment Platform</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:35px;">
                                <h2 style="margin-top:0;color:#1e293b;">{title}</h2>
                                <div style="white-space:pre-line;line-height:1.8;color:#334155;">
                                    {message}
                                </div>
                                {button_html}
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:20px;text-align:center;color:#64748b;font-size:12px;">
                                This is an automated message from AI Internship & Attachment System.<br>
                                Please do not reply directly to this email.
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def _send_email_via_brevo_api(config, subject, message, recipient_list, button_text=None, button_url=None):
    """Send email through Brevo's HTTPS API."""
    api_key = _get_brevo_api_key()
    if not api_key:
        raise ValueError('BREVO_API_KEY is not configured.')

    html_content = build_html_email(
        title=subject,
        message=message,
        button_text=button_text,
        button_url=button_url,
    )
    text_content = strip_tags(html_content)

    sender_value = _clean_setting(
        getattr(config, 'default_from_email', '')
        or os.environ.get('DEFAULT_FROM_EMAIL')
        or os.environ.get('EMAIL_FROM')
        or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    )

    if not sender_value:
        raise ValueError('DEFAULT_FROM_EMAIL is not configured.')

    sender_name, sender_email = parseaddr(sender_value)

    if not sender_email:
        raise ValueError('DEFAULT_FROM_EMAIL must contain a valid email address.')

    if not sender_name:
        sender_name = 'AI Internship & Attachment System'

    # Handle recipient list
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    # Clean recipients
    recipients = []
    for recipient in recipient_list:
        if recipient and recipient.strip():
            recipients.append({'email': recipient.strip()})

    if not recipients:
        raise ValueError('No valid recipients provided.')

    # Brevo API Payload
    payload = {
        'sender': {
            'name': sender_name,
            'email': sender_email,
        },
        'to': recipients,
        'subject': subject,
        'htmlContent': html_content,
        'textContent': text_content,
    }

    # Send via Brevo API
    response = requests.post(
        'https://api.brevo.com/v3/smtp/email',
        headers={
            'accept': 'application/json',
            'api-key': api_key,
            'content-type': 'application/json',
        },
        json=payload,
        timeout=60,
    )

    # Check response (201 = success)
    if response.status_code not in [200, 201]:
        error_message = response.text[:500]
        try:
            error_json = response.json()
            error_message = error_json.get('message', error_message)
        except:
            pass
        raise RuntimeError(f'Brevo API error {response.status_code}: {error_message}')

    return response


def _send_email_once(config, subject, message, recipient_list, button_text=None, button_url=None, allow_insecure_ssl=False):
    """Send email via SMTP"""
    connection = _build_connection(config, allow_insecure_ssl=allow_insecure_ssl)

    html_content = build_html_email(
        title=subject,
        message=message,
        button_text=button_text,
        button_url=button_url
    )

    text_content = strip_tags(html_content)

    from_email = getattr(config, 'default_from_email', None)
    if not from_email:
        from_email = os.environ.get('DEFAULT_FROM_EMAIL') or settings.DEFAULT_FROM_EMAIL

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_list,
        connection=connection,
    )

    email.attach_alternative(html_content, "text/html")
    email.send()


def get_active_email_config():
    """
    Get active email configuration.
    Priority: Brevo API > Environment > Database
    """

    # 1. Check if Brevo API is configured
    if _get_brevo_api_key():
        print("Using email config from BREVO_API")
        return SimpleNamespace(
            email_host='api.brevo.com',
            email_port=587,
            email_use_tls=True,
            email_host_user='',
            email_host_password='',
            default_from_email=_clean_setting(
                os.environ.get('DEFAULT_FROM_EMAIL')
                or os.environ.get('EMAIL_FROM')
                or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
            ),
            admin_notification_email=_clean_setting(
                os.environ.get('ADMIN_NOTIFICATION_EMAIL')
                or getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', '')
            ),
            source='BREVO_API',
            use_brevo_api=True,
        )

    # 2. Check environment variables for SMTP
    email_host = _clean_setting(
        os.environ.get('EMAIL_HOST')
        or os.environ.get('SMTP_HOST')
        or getattr(settings, 'EMAIL_HOST', '')
    )
    email_host_user = _clean_setting(
        os.environ.get('EMAIL_HOST_USER')
        or os.environ.get('SMTP_USER')
        or getattr(settings, 'EMAIL_HOST_USER', '')
    )
    email_host_password = _clean_setting(
        os.environ.get('EMAIL_HOST_PASSWORD')
        or os.environ.get('SMTP_PASS')
        or getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    )

    if all([email_host, email_host_user, email_host_password]):
        email_port = int(
            os.environ.get('EMAIL_PORT')
            or os.environ.get('SMTP_PORT')
            or getattr(settings, 'EMAIL_PORT', 587)
        )
        email_use_tls = str(
            os.environ.get('EMAIL_USE_TLS', getattr(settings, 'EMAIL_USE_TLS', True))
        ).strip().lower() in {'1', 'true', 'yes', 'on'}

        if email_port == 587:
            email_use_tls = True

        print(f"Using email config from ENVIRONMENT: {email_host}:{email_port}")
        return SimpleNamespace(
            email_host=email_host,
            email_port=email_port,
            email_use_tls=email_use_tls,
            email_host_user=email_host_user,
            email_host_password=email_host_password,
            default_from_email=_clean_setting(
                os.environ.get('DEFAULT_FROM_EMAIL')
                or os.environ.get('EMAIL_FROM')
                or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
                or email_host_user
            ),
            admin_notification_email=_clean_setting(
                os.environ.get('ADMIN_NOTIFICATION_EMAIL')
                or getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', '')
                or email_host_user
            ),
            source='ENVIRONMENT',
            use_brevo_api=False,
        )

    # 3. Fallback to database
    try:
        config = EmailConfiguration.objects.filter(is_active=True).first()
        if config:
            if int(config.email_port) == 587 and not config.email_use_tls:
                config.email_use_tls = True
            config.source = 'DATABASE'
            config.use_brevo_api = False
            print(f"Using email config from DATABASE: {config.email_host}:{config.email_port}")
            return config
    except Exception as e:
        print(f"Database email config error: {e}")

    print("ERROR: No email configuration found!")
    return None


def send_system_email(subject, message, recipient_list, button_text=None, button_url=None):
    """
    Send system email with logging and retry.
    """
    config = get_active_email_config()

    if config is None:
        # Log failure
        for recipient in recipient_list:
            try:
                EmailLog.objects.create(
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    status='failed',
                    error_message='No active email configuration found.'
                )
            except Exception:
                pass
        return False, 'No active email configuration found.'

    try:
        retry_message = ''

        # Use Brevo API if available
        if getattr(config, 'use_brevo_api', False) or _get_brevo_api_key():
            print("📧 Sending via Brevo API...")
            _send_email_via_brevo_api(
                config,
                subject,
                message,
                recipient_list,
                button_text=button_text,
                button_url=button_url,
            )
            retry_message = ' Sent via Brevo API.'
        else:
            # Use SMTP
            print("📧 Sending via SMTP...")
            try:
                _send_email_once(
                    config,
                    subject,
                    message,
                    recipient_list,
                    button_text=button_text,
                    button_url=button_url
                )
            except Exception as first_error:
                # Retry with insecure SSL if certificate error
                if not _is_certificate_verify_error(first_error):
                    raise

                retry_message = f' Certificate error, retried with insecure SSL.'
                _send_email_once(
                    config,
                    subject,
                    message,
                    recipient_list,
                    button_text=button_text,
                    button_url=button_url,
                    allow_insecure_ssl=True
                )

        # Log success
        for recipient in recipient_list:
            try:
                EmailLog.objects.create(
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    status='sent'
                )
            except Exception:
                pass

        print(f"✅ Email sent successfully to {len(recipient_list)} recipients")
        return True, f'Email sent successfully.{retry_message}'

    except Exception as error:
        print(f"❌ Failed to send email: {error}")

        # Log failure
        for recipient in recipient_list:
            try:
                EmailLog.objects.create(
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    status='failed',
                    error_message=str(error)
                )
            except Exception:
                pass

        return False, "Email delivery is temporarily unavailable. Please try again shortly."
