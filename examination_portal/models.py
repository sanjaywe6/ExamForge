"""
Examination Portal - Django Models
==================================
Complete database schema for server-rendered Examination Portal.

Design principles:
- Custom User with role-based access (CollegeAdmin, Teacher, Student)
- Proper ForeignKey/OneToOne relationships, no redundant FKs where derivable
- Unique constraints to prevent duplicate attempts
- Indexes on frequently queried fields
- Normalized: college derived via Teacher/Student, not duplicated on Exam
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.crypto import get_random_string
from django.core.validators import MinValueValidator


# -----------------------------------------------------------------------------
# Custom User & Role Management
# -----------------------------------------------------------------------------

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
    Custom User model.
    Why: Required for role-based access. Replaces username with email as primary identifier.
    """
    class Role(models.TextChoices):
        COLLEGE_ADMIN = "COLLEGE_ADMIN", "College Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    username = None  # Use email instead
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = CustomUserManager()

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
        ]


# -----------------------------------------------------------------------------
# College & Profile Models
# -----------------------------------------------------------------------------

class College(models.Model):
    """
    College/Institution.
    Why: Central entity. Teachers and Students belong to a college.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]


class Teacher(models.Model):
    """
    Teacher profile. Links User (with role=TEACHER) to College.
    Why: Teacher belongs to College; Teachers create Exams.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": CustomUser.Role.TEACHER},
    )
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="teachers",
    )
    employee_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["college", "employee_id"],
                condition=models.Q(employee_id__isnull=False) & ~models.Q(employee_id=""),
                name="unique_teacher_employee_per_college",
            ),
        ]
        indexes = [
            models.Index(fields=["college"]),
        ]


class Student(models.Model):
    """
    Student profile. Links User (with role=STUDENT) to College.
    Why: Student belongs to College; Students attempt Exams.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": CustomUser.Role.STUDENT},
    )
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="students",
    )
    roll_number = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["college", "roll_number"],
                condition=models.Q(roll_number__isnull=False) & ~models.Q(roll_number=""),
                name="unique_student_roll_per_college",
            ),
        ]
        indexes = [
            models.Index(fields=["college"]),
        ]


class CollegeAdmin(models.Model):
    """
    College Admin profile. Links User (with role=COLLEGE_ADMIN) to College.
    Why: CollegeAdmin manages a college; may handle result publishing, user management.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="college_admin_profile",
        limit_choices_to={"role": CustomUser.Role.COLLEGE_ADMIN},
    )
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="college_admins",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["college"]),
        ]
        verbose_name = "College Admin"
        verbose_name_plural = "College Admins"


# -----------------------------------------------------------------------------
# Exam & Questions
# -----------------------------------------------------------------------------

def generate_test_code():
    """Generate unique 8-char alphanumeric test code."""
    return get_random_string(8, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


class Exam(models.Model):
    """
    Exam/TestSeries. Created by Teacher.
    Why: Core entity for tests. Holds timing, marking, and result publishing control.
    """
    created_by = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="exams",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    test_code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        default=generate_test_code,
        editable=False,
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Duration in minutes",
    )
    positive_marking = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0)],
    )
    negative_marking = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Use 0 or negative value (e.g. -0.25)",
    )
    result_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F("start_time")),
                name="exam_end_after_start",
            ),
            models.CheckConstraint(
                check=models.Q(negative_marking__lte=0),
                name="exam_negative_marking_non_positive",
            ),
        ]
        indexes = [
            models.Index(fields=["start_time", "end_time"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["result_published"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.test_code})"


class Question(models.Model):
    """
    Question belonging to an Exam.
    Why: Stores question text, options, correct answer, and marks per question.
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    question_text = models.TextField()
    options = models.JSONField(
        default=dict,
        help_text='e.g. {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}',
    )
    correct_answer = models.CharField(max_length=10, help_text="Key from options, e.g. A")
    marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["exam", "order"]
        indexes = [
            models.Index(fields=["exam"]),
        ]


# -----------------------------------------------------------------------------
# Student Attempts & Answers
# -----------------------------------------------------------------------------

class StudentAttempt(models.Model):
    """
    One attempt per student per exam. Prevents duplicate attempts.
    Why: Tracks when student started/submitted; links to StudentAnswers.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "exam"],
                name="unique_student_exam_attempt",
            ),
        ]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["exam"]),
        ]


class StudentAnswer(models.Model):
    """
    Student's answer for a question within an attempt.
    Why: Stores selected option per question per attempt.
    """
    attempt = models.ForeignKey(
        StudentAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="student_answers",
    )
    selected_option = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_answer_per_question_per_attempt",
            ),
        ]
        indexes = [
            models.Index(fields=["attempt"]),
            models.Index(fields=["question"]),
        ]
