"""
Django settings for the config project.
"""

import os
from pathlib import Path

import certifi
from django.core.exceptions import ImproperlyConfigured


# ============================================================
# BASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# Load environment variables from backend/.env during local use.
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())


def env_bool(name, default=False):
    """
    Read a boolean environment variable safely.
    """

    default_value = "true" if default else "false"

    return (
        os.environ.get(name, default_value)
        .strip()
        .lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
    )


# ============================================================
# CORE SECURITY SETTINGS
# ============================================================

DEBUG = env_bool(
    "DJANGO_DEBUG",
    default=True,
)


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "",
).strip()

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = (
            "dev-only-insecure-key-change-before-production"
        )
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when "
            "DJANGO_DEBUG=False."
        )


_allowed_hosts_raw = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "",
).strip()

if _allowed_hosts_raw:
    ALLOWED_HOSTS = [
        host.strip()
        for host in _allowed_hosts_raw.split(",")
        if host.strip()
    ]
elif DEBUG:
    ALLOWED_HOSTS = [
        "127.0.0.1",
        "localhost",
    ]
else:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must be set when "
        "DJANGO_DEBUG=False."
    )


CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


PUBLIC_SITE_URL = os.environ.get(
    "PUBLIC_SITE_URL",
    (
        "http://127.0.0.1:8000"
        if DEBUG
        else ""
    ),
).rstrip("/")

if not DEBUG and not PUBLIC_SITE_URL:
    raise ImproperlyConfigured(
        "PUBLIC_SITE_URL must be set when "
        "DJANGO_DEBUG=False."
    )


# General browser security.
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = (
    "strict-origin-when-cross-origin"
)


# Production HTTPS security.
if not DEBUG:
    # Render terminates HTTPS at its reverse proxy.
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Begin with a short HSTS duration.
    # Increase only after HTTPS has been confirmed stable.
    SECURE_HSTS_SECONDS = int(
        os.environ.get(
            "SECURE_HSTS_SECONDS",
            "3600",
        )
    )

    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        default=False,
    )

    SECURE_HSTS_PRELOAD = env_bool(
        "SECURE_HSTS_PRELOAD",
        default=False,
    )


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "accounts",
    "students",
    "employers",
    "internships",
    "matching",
    "notifications",
    "institutions",
    "supervisors",
    "ai_assistant",
    "academics",
    "payments",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "accounts.middleware.DeviceAccessMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# Use WhiteNoise for production static files when installed.
try:
    import whitenoise  # noqa: F401

    MIDDLEWARE.insert(
        1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )

    WHITENOISE_AVAILABLE = True
except ImportError:
    WHITENOISE_AVAILABLE = False


ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django."
            "DjangoTemplates"
        ),
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                (
                    "django.template.context_processors."
                    "request"
                ),
                (
                    "django.contrib.auth.context_processors."
                    "auth"
                ),
                (
                    "django.contrib.messages."
                    "context_processors.messages"
                ),
                (
                    "notifications.context_processors."
                    "notification_count"
                ),
            ],
        },
    },
]


# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "",
).strip()

if DATABASE_URL:
    try:
        import dj_database_url
    except ImportError as exc:
        raise ImproperlyConfigured(
            "dj-database-url must be installed when "
            "DATABASE_URL is configured."
        ) from exc

    DATABASES["default"] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Nairobi"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


if WHITENOISE_AVAILABLE:
    STORAGES = {
        "default": {
            "BACKEND": (
                "django.core.files.storage."
                "FileSystemStorage"
            ),
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }


# ============================================================
# USER-UPLOADED MEDIA
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# Important:
# Render's filesystem is temporary unless persistent storage
# or an external media service is configured. Before accepting
# production uploads, configure Cloudinary, S3-compatible
# storage, or a Render persistent disk.


# ============================================================
# AUTHENTICATION
# ============================================================

AUTH_USER_MODEL = "accounts.User"


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]


LOGIN_URL = "login"

LOGIN_REDIRECT_URL = "dashboard"

LOGOUT_REDIRECT_URL = "login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# EMAIL AND PUBLIC URL SETTINGS
# ============================================================

PUBLIC_SITE_URL = os.environ.get(
    "SITE_URL",
    PUBLIC_SITE_URL,
).rstrip("/")


SITE_DOMAIN = os.environ.get(
    "SITE_DOMAIN",
    (
        "127.0.0.1:8000"
        if DEBUG
        else ""
    ),
).strip()


BREVO_API_KEY = os.environ.get(
    "BREVO_API_KEY",
    "",
).strip()


EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
).strip()


EMAIL_HOST = os.environ.get(
    "EMAIL_HOST",
    "",
).strip()


EMAIL_PORT = int(
    os.environ.get(
        "EMAIL_PORT",
        "587",
    )
)


EMAIL_USE_TLS = env_bool(
    "EMAIL_USE_TLS",
    default=True,
)


EMAIL_USE_SSL = env_bool(
    "EMAIL_USE_SSL",
    default=False,
)


if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured(
        "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both "
        "be enabled."
    )


EMAIL_HOST_USER = os.environ.get(
    "EMAIL_HOST_USER",
    "",
).strip()


EMAIL_HOST_PASSWORD = os.environ.get(
    "EMAIL_HOST_PASSWORD",
    "",
).strip()


DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    (
        "Commercial-Grade AI-Powered Internship "
        "Management System "
        "<georgesultan931@gmail.com>"
    ),
).strip()


SERVER_EMAIL = os.environ.get(
    "SERVER_EMAIL",
    "georgesultan931@gmail.com",
).strip()


EMAIL_REPLY_TO = os.environ.get(
    "EMAIL_REPLY_TO",
    "georgesultan931@gmail.com",
).strip()


ADMIN_NOTIFICATION_EMAIL = os.environ.get(
    "ADMIN_NOTIFICATION_EMAIL",
    "georgesultan931@gmail.com",
).strip()


EMAIL_ALLOW_INSECURE_SMTP_SSL = False


# ============================================================
# SESSION AND CSRF SETTINGS
# ============================================================

SESSION_COOKIE_AGE = 1209600

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

SESSION_SAVE_EVERY_REQUEST = True


CSRF_COOKIE_HTTPONLY = False

CSRF_COOKIE_SAMESITE = "Lax"

CSRF_USE_SESSIONS = False


# Keep local HTTP development working.
if DEBUG:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False


# ============================================================
# PASSWORD RESET AND FRONTEND URLS
# ============================================================

FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    PUBLIC_SITE_URL,
).rstrip("/")


# ============================================================
# COMMERCIAL-GRADE AI ASSISTANT
# ============================================================

# The Gemini key remains on the Django server.
# Never expose it in templates or browser JavaScript.
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "",
).strip()


GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
).strip()


# ============================================================
# PRODUCTION LOGGING
# ============================================================

# ============================================================
# M-PESA DARAJA SETTINGS
# ============================================================

MPESA_ENVIRONMENT = os.environ.get(
    "MPESA_ENVIRONMENT",
    "sandbox",
).strip().lower()

MPESA_CONSUMER_KEY = os.environ.get(
    "MPESA_CONSUMER_KEY",
    "",
).strip()

MPESA_CONSUMER_SECRET = os.environ.get(
    "MPESA_CONSUMER_SECRET",
    "",
).strip()

MPESA_SHORTCODE = os.environ.get(
    "MPESA_SHORTCODE",
    "174379",
).strip()

MPESA_PASSKEY = os.environ.get(
    "MPESA_PASSKEY",
    "",
).strip()

MPESA_CALLBACK_URL = os.environ.get(
    "MPESA_CALLBACK_URL",
    "",
).strip()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": (
                "{levelname} {asctime} "
                "{name} {message}"
            ),
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },

    "root": {
        "handlers": [
            "console",
        ],
        "level": (
            "DEBUG"
            if DEBUG
            else "INFO"
        ),
    },

    "loggers": {
        "django": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propagate": False,
        },

        "django.request": {
            "handlers": [
                "console",
            ],
            "level": "ERROR",
            "propagate": False,
        },

        "django.db.backends": {
            "handlers": [
                "console",
            ],
            "level": "WARNING",
            "propagate": False,
        },

        "django.template": {
            "handlers": [
                "console",
            ],
            "level": "WARNING",
            "propagate": False,
        },
    },
}