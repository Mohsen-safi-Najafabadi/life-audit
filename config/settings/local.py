"""Development settings. Never used in production."""

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Print emails to the terminal instead of sending them.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"