"""
Exam and Question models. Teacher creates exams; questions from CSV or manual.
"""
from django.db import models
from django.utils.crypto import get_random_string
from django.core.validators import MinValueValidator


def generate_test_code():
    """Generate unique 8-char alphanumeric test code."""
    return get_random_string(8, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


class Exam(models.Model):
    created_by = models.ForeignKey(
        "colleges.Teacher",
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

    def save(self, *args, **kwargs):
        if not self.test_code:
            for _ in range(10):
                code = generate_test_code()
                if not Exam.objects.filter(test_code=code).exists():
                    self.test_code = code
                    break
            else:
                self.test_code = generate_test_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.test_code})"


class Question(models.Model):
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
        indexes = [models.Index(fields=["exam"])]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."
