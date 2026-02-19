# Exam Creation & CSV Validation Flow

## Overview

1. **Exam creation** — Teacher submits exam details (and optionally a CSV). Form and CSV are validated; on success, exam and questions are saved inside a single `transaction.atomic()`.
2. **Upload questions** — Teacher selects an existing exam and uploads a CSV. CSV is validated; on success, questions are bulk-created inside `transaction.atomic()`.

---

## Validation Flow (Create Exam)

```
POST /exams/create/
    │
    ├─► Bind ExamCreationForm(request.POST)
    ├─► If request.FILES has "csv_file":
    │       validate_questions_csv(csv_file)  → (rows, errors)
    │
    ├─► If form.is_valid() and no csv_errors:
    │       transaction.atomic():
    │           exam = form.save(commit=False)
    │           exam.created_by = current_teacher
    │           exam.save()   # test_code set in Exam.save() if missing
    │           for each row in csv_rows:
    │               Question.objects.create(exam=exam, ...)
    │       messages.success → redirect to exam detail
    │
    └─► Else:
            Re-display form with errors; show CSV errors as messages
```

- **Exam form validation:** title, start_time, end_time (end > start), duration_minutes ≥ 1, positive_marking ≥ 0, negative_marking ≤ 0.
- **CSV validation:** See "CSV validation (strict)" below. Any row or header error aborts the CSV part; all errors are shown; no partial save.

---

## Validation Flow (Upload Questions to Existing Exam)

```
POST /exams/<id>/upload-questions/
    │
    ├─► Load exam; ensure exam.created_by == current_teacher
    ├─► Bind QuestionCSVUploadForm(data=POST, files=FILES, exam=exam)
    │       clean_csv_file() calls validate_questions_csv() and sets _validated_rows
    │
    ├─► If form.is_valid():
    │       transaction.atomic():
    │           for each row in form._validated_rows:
    │               Question.objects.create(exam=exam, ...)
    │       messages.success → redirect to exam detail
    │
    └─► Else: show form with field errors (and messages for each error)
```

---

## CSV Validation (Strict)

Implemented in `exams/forms.validate_questions_csv(file)` using **Pandas**:

1. **File type** — Must have `.csv` extension.
2. **Read** — `pd.read_csv(file, dtype=str, keep_default_na=False)` so all cells are strings and empty cells are `""`.
3. **Columns** — Exact set required; no extra columns allowed.
   - **Required columns:** `order`, `question_text`, `option_a`, `option_b`, `option_c`, `option_d`, `correct_answer`, `marks`
   - Missing column → single error listing required columns.
   - Unexpected column → error listing allowed columns.
4. **Per row (for each data row):**
   - **order** — Required; must be integer ≥ 1.
   - **question_text** — Required; non-empty after strip.
   - **option_a, option_b, option_c, option_d** — All required; non-empty after strip.
   - **correct_answer** — Required; must be one of `A`, `B`, `C`, `D` (case-insensitive).
   - **marks** — Required; must be a valid decimal number ≥ 0.
5. **Output** — Returns `(rows, errors)`. Only rows that pass all checks are in `rows`. Any validation failure for a row adds a message to `errors` (with row number, 1-based, header = row 1).

No data is written to the DB until both form and CSV (if provided) pass; then a single `transaction.atomic()` is used for exam + questions or for bulk questions only.

---

## test_code Generation

- **Exam.save():** If `test_code` is empty, generate via `get_random_string(8, allowed_chars="A-Z0-9" no 0/O/1/I)` and ensure uniqueness by checking `Exam.objects.filter(test_code=code).exists()`; retry up to 10 times, then fallback to one more random code.
- Set before `super().save()` so the exam is stored with a unique code.

---

## Success / Error Messages

- **Success:** "Exam '…' created with test code XXXXXXXX. N question(s) added from CSV." or "N question(s) added to exam."
- **Errors:** Form errors shown on form; CSV errors and other errors shown via `messages.error()` so they appear in the messages block on the same or next page.
