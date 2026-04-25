import os

from config.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ["0.0.0.0", "localhost", "127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = "no-reply@jaksim.com"

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

INTERNAL_IPS = ["127.0.0.1"]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://oz-union-16-fe-team2.vercel.app",
    "http://jaksim.duckdns.org",
]
CORS_ALLOW_CREDENTIALS = True

COOKIE_SECURE = False
COOKIE_SAME_SITE = "Lax"
