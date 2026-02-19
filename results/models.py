"""
StudentAttempt: one per student per exam. Scores stored on submit (prevent tampering).
StudentAnswer: one per question per attempt.
"""
from decimal import Decimal
from django.db import models


class StudentAttempt(models.Model):
    student = models.ForeignKey(
        "colleges.Student",
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    exam = models.ForeignKey(
        "exams.Exam",
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    total_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Computed once on submit; do not edit.",
    )
    max_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Sum of question marks; set on submit.",
    )

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

    def __str__(self):
        return f"{self.student} – {self.exam}"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(
        StudentAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        "exams.Question",
        on_delete=models.CASCADE,
        related_name="student_answers",
    )
    selected_option = models.CharField(max_length=10, blank=True)
    marked_for_review = models.BooleanField(default=False)
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
