# Evaluation & result publishing — security protections

## 1. Score calculation and storage (prevent tampering)

- **Single computation at submit:** Total and max scores are computed only once, when the student submits the exam, inside a `transaction.atomic()` block together with setting `submitted_at`, `total_score`, and `max_score` on `StudentAttempt`.
- **Stored scores only:** All “result” views (teacher and student) display the stored `total_score` and `max_score` from the database. Scores are never recomputed from `StudentAnswer` rows for display. So changing answers after submission does not change the shown score.
- **No direct score editing in app:** There is no form or view that lets a user (student or teacher) edit `total_score` or `max_score`. Changing them would require DB/admin access.

## 2. Evaluation logic (negative marking)

- **Correct:** `selected_option == question.correct_answer` → add `question.marks`.
- **Wrong:** Student chose A/B/C/D but it’s wrong → add `exam.negative_marking` (0 or negative).
- **Unattempted:** No choice or blank → add 0.
- **Max score:** Sum of `question.marks` over all questions of the exam. Stored once at submit.

## 3. Transaction.atomic

- On submit, in one `transaction.atomic()` block we:
  - Compute `total_score` and `max_score` via `compute_attempt_score(attempt)` (read-only over attempts/answers/questions/exam).
  - Update `StudentAttempt`: `submitted_at`, `total_score`, `max_score`.
- So we never persist “submitted” without scores, or scores without “submitted”.

## 4. Who can see results

- **Teacher (exam owner):** Can view all attempts for their exams (with scores) at any time via “View all attempts”. No dependency on `result_published`.
- **Student:** Can see their own score for an attempt only if:
  - They are logged in and the attempt belongs to their student profile (`attempt.student_id == request.user.student_profile.pk`).
  - The exam’s `result_published` is True. Otherwise they see “Results not published yet” and are not shown the score.

## 5. Publishing (teacher only)

- Only a teacher who created the exam can publish: `exam.created_by_id == request.user.teacher_profile.pk`. The publish action is a POST to a dedicated URL; there is no “unpublish” in the current flow.
- After publish, students see stored scores only; no recalculation.

## 6. Summary

| Risk | Mitigation |
|------|------------|
| Score changed after submit | Scores computed and saved once in atomic block; only stored values are shown. |
| Student sees others’ results | Filter by `attempt.student_id == current student`; student views only list their attempts. |
| Student sees result before publish | Check `exam.result_published`; if False, redirect/list shows “not published” and detail view is forbidden. |
| Non-owner teacher sees/publishes | Exam views check `exam.created_by_id == teacher.pk`. |
| Partial or inconsistent submit | Single `transaction.atomic()` for submitted_at + total_score + max_score. |
