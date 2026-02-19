"""
Production settings.
Override in environment: DJANGO_SECRET_KEY, DJANGO_DEBUG=False, DJANGO_ALLOWED_HOSTS, DATABASE_URL, etc.
"""
from .base import *

DEBUG = False
