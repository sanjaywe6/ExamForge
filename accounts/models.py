"""
Custom User model for Examination Portal.
Session-based auth; password hashing via Django (PBKDF2).
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    """Custom manager for CustomUser with email-as-username support."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.Role.COLLEGE_ADMIN)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom User. Email as USERNAME_FIELD; role for College Admin / Teacher / Student.
    """
    class Role(models.TextChoices):
        COLLEGE_ADMIN = "COLLEGE_ADMIN", "College Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = CustomUserManager()

    class Meta:
        indexes = [models.Index(fields=["role"])]

    def __str__(self):
        return self.email
