"""
Django settings for main project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import dj_database_url
import os
from pathlib import Path
from decouple import config
from django.test.runner import DiscoverRunner

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent

IS_HEROKU = "DYNO" in os.environ


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

if IS_HEROKU:
    DEBUG = False
else:
    DEBUG = True

if IS_HEROKU:
    # Allowing for secure communication on heroku
    ALLOWED_HOSTS = ["*"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True

    # improving security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 15768000  # 1/2 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    ALLOWED_HOSTS = []
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "csp",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
    "ninja",
    "qlued",
    "frontend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "main.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

MAX_CONN_AGE = 600

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


if IS_HEROKU and "DATABASE_URL" in os.environ:
    # Configure Django for DATABASE_URL environment variable.
    DATABASES["default"] = dj_database_url.config(
        conn_max_age=MAX_CONN_AGE, ssl_require=True
    )

    # Enable test database if found in CI environment.
    if "CI" in os.environ:
        DATABASES["default"]["TEST"] = DATABASES["default"]  # type: ignore[assignment]


# Media files
# https://docs.djangoproject.com/en/dev/topics/files/
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)


# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"

# Enable WhiteNoise's GZip compression of static assets, but only within Heroku
if IS_HEROKU:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Test Runner Config
class HerokuDiscoverRunner(DiscoverRunner):
    """Test Runner for Heroku CI, which provides a database for you.
    This requires you to set the TEST database (done for you by settings().)"""

    def setup_databases(self, **kwargs):
        self.keepdb = True
        return super(HerokuDiscoverRunner, self).setup_databases(**kwargs)


# Use HerokuDiscoverRunner on Heroku CI
if IS_HEROKU and "CI" in os.environ:
    TEST_RUNNER = "main.settings.HerokuDiscoverRunner"


# social account login etc
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = "none"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "index"
ACCOUNT_LOGOUT_ON_GET = True

# Content Security Policy (CSP)
CSP_REPORT_ONLY = True


CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://django-ninja.rest-framework.com/img/favicon.png",
)
CSP_STYLE_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css",
    "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui.css",
)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js",
    "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-bundle.js",
)

CSP_INCLUDE_NONCE_IN = {
    "script-src": ["<nonce>"],
}
