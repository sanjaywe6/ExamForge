"""
Evaluation logic: compute total_score and max_score for a submitted attempt.
Applied once on submit inside transaction.atomic(); result stored to prevent tampering.
"""
from decimal import Decimal


def compute_attempt_score(attempt):
    """
    Compute total_score and max_score for an attempt.
    - Correct answer: + question.marks
    - Wrong answer: + exam.negative_marking (0 or negative)
    - Unattempted: 0
    Returns (total_score, max_score).
    """
    exam = attempt.exam
    questions = list(exam.questions.all())
    answer_by_question = {a.question_id: a for a in attempt.answers.select_related("question").all()}

    total = Decimal("0")
    max_total = Decimal("0")
    for q in questions:
        max_total += q.marks
        ans = answer_by_question.get(q.id)
        selected = (ans.selected_option or "").strip().upper() if ans else ""
        correct_key = (q.correct_answer or "").strip().upper()
        if selected == correct_key and selected:
            total += q.marks
        elif selected and selected in ("A", "B", "C", "D"):
            total += exam.negative_marking
        # else: unattempted, add 0

    return (total, max_total)
