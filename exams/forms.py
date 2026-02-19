"""
Exam creation and CSV question upload forms with strict validation.
"""
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation

from .models import Exam, Question


# Required CSV columns (strict format)
CSV_REQUIRED_COLUMNS = [
    "order",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_answer",
    "marks",
]


def validate_questions_csv(file):
    """
    Strict CSV validation using Pandas. Returns (cleaned_rows, errors).
    - File must have exactly these columns: order, question_text, option_a, option_b, option_c, option_d, correct_answer, marks.
    - No empty required cells; correct_answer in A,B,C,D; order/marks valid numbers.
    """
    import pandas as pd

    errors = []
    rows = []

    if not file.name.lower().endswith(".csv"):
        return [], ["File must be a CSV (.csv)."]

    try:
        df = pd.read_csv(file, dtype=str, keep_default_na=False)
    except Exception as e:
        return [], [f"Could not read CSV: {str(e)}"]

    # Strip column names and check
    df.columns = df.columns.str.strip()
    missing = [c for c in CSV_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return [], [f"Missing required columns: {', '.join(missing)}. Required: {', '.join(CSV_REQUIRED_COLUMNS)}."]
    extra = [c for c in df.columns if c not in CSV_REQUIRED_COLUMNS]
    if extra:
        return [], [f"Unexpected columns: {', '.join(extra)}. Only these are allowed: {', '.join(CSV_REQUIRED_COLUMNS)}."]

    allowed_answers = {"A", "B", "C", "D"}

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-based and header is row 1
        try:
            order_val = (row.get("order") or "").strip()
            if not order_val:
                errors.append(f"Row {row_num}: 'order' is required.")
                continue
            try:
                order = int(order_val)
            except ValueError:
                errors.append(f"Row {row_num}: 'order' must be an integer.")
                continue
            if order < 1:
                errors.append(f"Row {row_num}: 'order' must be >= 1.")
                continue

            question_text = (row.get("question_text") or "").strip()
            if not question_text:
                errors.append(f"Row {row_num}: 'question_text' is required.")
                continue

            option_a = (row.get("option_a") or "").strip()
            option_b = (row.get("option_b") or "").strip()
            option_c = (row.get("option_c") or "").strip()
            option_d = (row.get("option_d") or "").strip()
            if not all([option_a, option_b, option_c, option_d]):
                errors.append(f"Row {row_num}: All options (option_a, option_b, option_c, option_d) are required.")
                continue

            correct = (row.get("correct_answer") or "").strip().upper()
            if correct not in allowed_answers:
                errors.append(f"Row {row_num}: 'correct_answer' must be one of A, B, C, D (got '{correct}').")
                continue

            marks_val = (row.get("marks") or "").strip()
            if not marks_val:
                errors.append(f"Row {row_num}: 'marks' is required.")
                continue
            try:
                marks = Decimal(marks_val)
            except (InvalidOperation, ValueError):
                errors.append(f"Row {row_num}: 'marks' must be a valid number.")
                continue
            if marks < 0:
                errors.append(f"Row {row_num}: 'marks' must be >= 0.")
                continue

            rows.append({
                "order": order,
                "question_text": question_text,
                "options": {"A": option_a, "B": option_b, "C": option_c, "D": option_d},
                "correct_answer": correct,
                "marks": marks,
            })
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    return rows, errors


class ExamCreationForm(forms.ModelForm):
    """Teacher creates exam: title, times, duration, marking."""

    class Meta:
        model = Exam
        fields = [
            "title",
            "description",
            "positive_marking",
            "negative_marking",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Exam title"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Optional description"}),
        }
    def clean_negative_marking(self):
        val = self.cleaned_data.get("negative_marking")
        if val is not None and val > 0:
            raise ValidationError("Negative marking must be 0 or negative (e.g. -0.25).")
        return val


class QuestionCSVUploadForm(forms.Form):
    """Upload CSV to add questions to an existing exam."""
    csv_file = forms.FileField(
        label="CSV file",
        help_text="Required columns: order, question_text, option_a, option_b, option_c, option_d, correct_answer, marks",
    )

    def __init__(self, exam=None, *args, **kwargs):
        self.exam = exam
        super().__init__(*args, **kwargs)

    def clean_csv_file(self):
        file = self.cleaned_data.get("csv_file")
        if not file:
            return file
        rows, errors = validate_questions_csv(file)
        if errors:
            raise ValidationError(errors)
        if not rows:
            raise ValidationError("CSV has no valid question rows.")
        self._validated_rows = rows
        file.seek(0)
        return file


class ExamEntryForm(forms.Form):
    """Student exam entry: test code, registration number, date of birth."""
    test_code = forms.CharField(
        max_length=8,
        label="Test code",
        widget=forms.TextInput(attrs={"placeholder": "e.g. ABCD1234", "autocomplete": "off"}),
    )
    registration_number = forms.CharField(
        max_length=50,
        label="Registration / Roll number",
        widget=forms.TextInput(attrs={"placeholder": "Your roll number"}),
    )
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    college_code = forms.CharField(
        max_length=50,
        label="College code",
        widget=forms.TextInput(attrs={"placeholder": "College code (e.g. ABC)"}),
    )
