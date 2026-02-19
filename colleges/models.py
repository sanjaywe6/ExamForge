"""
College, Teacher, Student, CollegeAdmin.
Teachers and Students are created by College Admin.
"""
from django.db import models
from django.conf import settings


class College(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StudentBatch(models.Model):
    """Groups students imported in a single batch with title and description."""
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="student_batches",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["college"])]

    def __str__(self):
        return f"{self.title} ({self.college.name})"


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": "TEACHER"},
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
        indexes = [models.Index(fields=["college"])]

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": "STUDENT"},
    )
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="students",
    )
    batch = models.ForeignKey(
        StudentBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    student_id = models.CharField(max_length=50, null=True, blank=True, db_index=True, unique=True)
    course = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True, help_text="Used for exam entry verification")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["college", "student_id"],
                condition=models.Q(student_id__isnull=False) & ~models.Q(student_id=""),
                name="unique_student_roll_per_college",
            ),
        ]
        indexes = [models.Index(fields=["college"])]

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class CollegeAdmin(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="college_admin_profile",
        limit_choices_to={"role": "COLLEGE_ADMIN"},
    )
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="college_admins",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["college"])]
        verbose_name = "College Admin"
        verbose_name_plural = "College Admins"

    def __str__(self):
        return self.user.get_full_name() or self.user.email
