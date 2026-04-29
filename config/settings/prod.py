import os

from config.settings.base import *

DEBUG = False

ALLOWED_HOSTS = ["jaksim.duckdns.org", "localhost", "127.0.0.1", "54.180.232.189"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

SIMPLE_JWT_REFRESH_COOKIE = "refresh_token"

COOKIE_SECURE = True
COOKIE_SAME_SITE = "None"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

FRONTEND_BASE_URL = os.environ.get(
    "FRONTEND_BASE_URL",
    "https://oz-union-16-fe-team2.vercel.app",
)
