"""
Development settings.
"""
from .base import *

DEBUG = True

# CSRF settings for development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://127.0.0.1",
]

# Session settings for development
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True
# Keep users logged in across browser restarts unless they explicitly logout.
# Default session age: 2 weeks
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
# Do not expire the session at browser close
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# Refresh session expiry on each request (keeps active users logged in)
SESSION_SAVE_EVERY_REQUEST = True