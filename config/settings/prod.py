import os

from config.settings.base import *

DEBUG = False

ALLOWED_HOSTS = ["jaksim.duckdns.org/api/docsoz-union-16-fe-team2.vercel.applocalhost", "127.0.0.1", "54.180.232.189"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_CREDENTIALS = True

SIMPLE_JWT_REFRESH_COOKIE = "refresh_token"

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
