from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path.cwd()

if not (ROOT / "manage.py").exists():
    print("ERROR: Run this installer from the backend folder containing manage.py.")
    sys.exit(1)

print("Installing Step 6 - Email & Notification Hardening...")

backup_dir = ROOT / "step6_backup"
backup_dir.mkdir(exist_ok=True)

targets = [
    ROOT / "notifications" / "email_service.py",
    ROOT / "accounts" / "views.py",
    ROOT / "accounts" / "urls.py",
    ROOT / "templates" / "accounts" / "pending_approval.html",
]

for target in targets:
    if target.exists():
        safe_name = str(target.relative_to(ROOT)).replace("\\", "__").replace("/", "__")
        shutil.copy2(target, backup_dir / f"{safe_name}.before_step6")

# 1. notifications/email_service.py
email_service = ROOT / "notifications" / "email_service.py"
text = email_service.read_text(encoding="utf-8")

if "USER_SAFE_EMAIL_FAILURE" not in text:
    anchor = "from .models import EmailConfiguration, EmailLog\n"
    if anchor not in text:
        raise RuntimeError("Could not patch notifications/email_service.py imports.")
    text = text.replace(
        anchor,
        anchor + '\nUSER_SAFE_EMAIL_FAILURE = "Email delivery is temporarily unavailable. Please try again shortly."\n',
        1,
    )

text = text.replace(
    "return False, 'No active email configuration found.'",
    "return False, USER_SAFE_EMAIL_FAILURE",
)

text = text.replace(
    "        return False, str(error)\n",
    "        return False, USER_SAFE_EMAIL_FAILURE\n",
    1,
)

email_service.write_text(text, encoding="utf-8")

# 2. accounts/views.py
views_path = ROOT / "accounts" / "views.py"
text = views_path.read_text(encoding="utf-8")

if "from django.core.cache import cache" not in text:
    anchor = "from django.core import signing\n"
    if anchor in text:
        text = text.replace(anchor, anchor + "from django.core.cache import cache\n", 1)
    else:
        idx = text.find("from django")
        if idx == -1:
            raise RuntimeError("Could not find Django imports in accounts/views.py.")
        text = text[:idx] + "from django.core.cache import cache\n" + text[idx:]

if "def resend_verification_email(request):" not in text:
    marker = "\ndef pending_approval(request):"
    if marker not in text:
        raise RuntimeError("Could not find pending_approval() in accounts/views.py.")
    text = text.replace(marker, '\ndef resend_verification_email(request):\n    """Safely resend a registration verification email."""\n    if request.method != "POST":\n        return redirect("pending_approval")\n\n    email = (request.POST.get("email") or "").strip().lower()\n    generic_message = (\n        "If that address belongs to an unverified account, "\n        "a new verification email has been sent."\n    )\n\n    if not email:\n        messages.info(request, generic_message)\n        return redirect("pending_approval")\n\n    cooldown_key = f"verification-resend:{email}"\n\n    if cache.get(cooldown_key):\n        messages.info(\n            request,\n            "A verification email was requested recently. "\n            "Please wait about a minute before trying again.",\n        )\n        return redirect("pending_approval")\n\n    cache.set(cooldown_key, True, timeout=60)\n\n    user = User.objects.filter(email__iexact=email).first()\n\n    if user and not getattr(user, "is_email_verified", False):\n        try:\n            sent, delivery_message = send_registration_received_notification(user)\n            if not sent:\n                logger.warning(\n                    "Verification resend failed for user_id=%s email=%s: %s",\n                    user.id,\n                    user.email,\n                    delivery_message,\n                )\n        except Exception:\n            logger.exception(\n                "Verification resend raised an exception for user_id=%s email=%s",\n                user.id,\n                user.email,\n            )\n\n    messages.info(request, generic_message)\n    return redirect("pending_approval")\n\n' + marker, 1)

views_path.write_text(text, encoding="utf-8")

# 3. accounts/urls.py
urls_path = ROOT / "accounts" / "urls.py"
text = urls_path.read_text(encoding="utf-8")

if "resend_verification_email" not in text:
    anchor = "    path('pending-approval/', views.pending_approval, name='pending_approval'),\n"
    if anchor not in text:
        raise RuntimeError("Could not find pending-approval route in accounts/urls.py.")
    text = text.replace(
        anchor,
        anchor + "    path('resend-verification/', views.resend_verification_email, name='resend_verification_email'),\n",
        1,
    )

urls_path.write_text(text, encoding="utf-8")

# 4. pending_approval.html
template_path = ROOT / "templates" / "accounts" / "pending_approval.html"
text = template_path.read_text(encoding="utf-8")

text = re.sub(
    r"\s*\{% if registration_email_message %\}\s*<hr>\s*<small>\{\{ registration_email_message \}\}</small>\s*\{% endif %\}",
    "",
    text,
    flags=re.S,
)

text = text.replace(
    "Your account was created, but the verification email could not be delivered. Admin should open Email logs and check the latest error message.",
    "Your account was created successfully, but the verification email could not be delivered right now. Please try resending it below.",
)

text = text.replace(
    "Email delivery configuration is not ready. If you are testing locally, check your PowerShell terminal for the verification link.",
    "Email delivery is temporarily unavailable. Please try again shortly.",
)

if "resend_verification_email" not in text:
    anchor = """            <a href="{% url 'login' %}" class="btn btn-primary btn-lg w-100">
                Back to Login
            </a>"""
    if anchor not in text:
        raise RuntimeError("Could not find Back to Login button in pending_approval.html.")
    text = text.replace(anchor, '            {% if not registration_review_message %}\n                <div class="mt-4 mb-3 text-start">\n                    <div class="border rounded-4 p-3 bg-light">\n                        <strong class="d-block mb-2">Didn\'t receive the verification email?</strong>\n\n                        <form method="post" action="{% url \'resend_verification_email\' %}">\n                            {% csrf_token %}\n                            <label for="resend-email" class="form-label small text-muted">\n                                Enter the email address used during registration.\n                            </label>\n\n                            <div class="input-group">\n                                <input\n                                    id="resend-email"\n                                    type="email"\n                                    name="email"\n                                    class="form-control"\n                                    placeholder="you@example.com"\n                                    required\n                                    autocomplete="email"\n                                >\n                                <button class="btn btn-outline-primary" type="submit">\n                                    Resend\n                                </button>\n                            </div>\n\n                            <small class="text-muted d-block mt-2">\n                                For security, resend requests are limited to once per minute.\n                            </small>\n                        </form>\n                    </div>\n                </div>\n            {% endif %}\n\n            <a href="{% url \'login\' %}" class="btn btn-primary btn-lg w-100">\n                Back to Login\n            </a>', 1)

template_path.write_text(text, encoding="utf-8")

print("Step 6 source patches applied.")
print("Running Django check...")

result = subprocess.run([sys.executable, "manage.py", "check"], cwd=ROOT)

if result.returncode != 0:
    print("\nDjango check failed.")
    print("Restore from .\\step6_backup if needed.")
    sys.exit(result.returncode)

print("\nStep 6 installed successfully.")
print("Backup created in .\\step6_backup")
print("\nNext run:")
print("  python manage.py test matching")
print("  python manage.py runserver")
