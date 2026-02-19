"""
Teacher exam creation and student exam attempt flow.
Student entry: test code + registration number + DOB; validate time window; prevent re-attempt.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser
from results.models import StudentAttempt, StudentAnswer

from .models import Exam, Question
from .forms import (
    ExamCreationForm,
    QuestionCSVUploadForm,
    ExamEntryForm,
    validate_questions_csv,
)


def get_teacher_or_redirect(request):
    """Return Teacher for request.user or None; redirect if not teacher."""
    if request.user.role != CustomUser.Role.TEACHER:
        messages.error(request, "Access denied. Teachers only.")
        return None
    try:
        return request.user.teacher_profile
    except Exception:
        messages.error(request, "Teacher profile not found.")
        return None


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
@csrf_protect
def exam_create_view(request):
    """Create exam with optional CSV: validate exam form and CSV, then atomic create exam + questions."""
    teacher = get_teacher_or_redirect(request)
    if teacher is None:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = ExamCreationForm(data=request.POST)
        csv_file = request.FILES.get("csv_file")
        csv_rows, csv_errors = [], []

        if csv_file:
            csv_rows, csv_errors = validate_questions_csv(csv_file)

        if form.is_valid() and not csv_errors:
            try:
                with transaction.atomic():
                    exam = form.save(commit=False)
                    exam.created_by = teacher
                    exam.save()
                    for row in csv_rows:
                        Question.objects.create(
                            exam=exam,
                            order=row["order"],
                            question_text=row["question_text"],
                            options=row["options"],
                            correct_answer=row["correct_answer"],
                            marks=row["marks"],
                        )
                msg = f"Exam '{exam.title}' created with test code {exam.test_code}."
                if csv_rows:
                    msg += f" {len(csv_rows)} question(s) added from CSV."
                messages.success(request, msg)
                return redirect("exams:exam_detail", exam_id=exam.pk)
            except Exception as e:
                messages.error(request, f"Could not save exam: {str(e)}")
        else:
            if csv_errors:
                for err in csv_errors:
                    messages.error(request, err)
            if not form.is_valid():
                messages.error(request, "Please correct the exam form errors below.")
    else:
        form = ExamCreationForm()

    return render(request, "exams/exam_create.html", {"form": form})


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
@csrf_protect
def exam_upload_questions_view(request, exam_id):
    """Upload CSV to add questions to an existing exam. Atomic bulk create."""
    teacher = get_teacher_or_redirect(request)
    if teacher is None:
        return redirect("accounts:dashboard")

    exam = get_object_or_404(Exam, pk=exam_id)
    if exam.created_by_id != teacher.pk:
        messages.error(request, "You can only add questions to your own exams.")
        return redirect("exams:exam_list")

    if request.method == "POST":
        form = QuestionCSVUploadForm(exam=exam, data=request.POST, files=request.FILES)
        if form.is_valid():
            rows = form._validated_rows
            try:
                with transaction.atomic():
                    for row in rows:
                        Question.objects.create(
                            exam=exam,
                            order=row["order"],
                            question_text=row["question_text"],
                            options=row["options"],
                            correct_answer=row["correct_answer"],
                            marks=row["marks"],
                        )
                messages.success(request, f"{len(rows)} question(s) added to exam.")
                return redirect("exams:exam_detail", exam_id=exam.pk)
            except Exception as e:
                messages.error(request, f"Could not save questions: {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, err)
    else:
        form = QuestionCSVUploadForm(exam=exam)

    return render(request, "exams/exam_upload_questions.html", {"form": form, "exam": exam})


@login_required(login_url="accounts:login")
def exam_list_view(request):
    """List exams created by the current teacher."""
    teacher = get_teacher_or_redirect(request)
    if teacher is None:
        return redirect("accounts:dashboard")
    exams = Exam.objects.filter(created_by=teacher).order_by("-start_time")
    return render(request, "exams/exam_list.html", {"exams": exams})


@login_required(login_url="accounts:login")
def exam_detail_view(request, exam_id):
    """Show exam details and question count; link to upload CSV."""
    teacher = get_teacher_or_redirect(request)
    if teacher is None:
        return redirect("accounts:dashboard")
    exam = get_object_or_404(Exam, pk=exam_id)
    if exam.created_by_id != teacher.pk:
        messages.error(request, "Access denied.")
        return redirect("exams:exam_list")
    question_count = exam.questions.count()
    return render(request, "exams/exam_detail.html", {"exam": exam, "question_count": question_count})


@login_required(login_url="accounts:login")
def exam_attempts_list_view(request, exam_id):
    """Teacher: view all attempts for this exam (with scores)."""
    teacher = get_teacher_or_redirect(request)
    if teacher is None:
        return redirect("accounts:dashboard")
    exam = get_object_or_404(Exam, pk=exam_id)
    if exam.created_by_id != teacher.pk:
        messages.error(request, "Access denied.")
        return redirect("exams:exam_list")
    attempts = exam.attempts.select_related("student", "student__user").order_by("-submitted_at")
    return render(request, "exams/exam_attempts_list.html", {"exam": exam, "attempts": attempts})


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
@csrf_protect
def exam_publish_results_view(request, exam_id):
    """Teacher: publish results (students can then see scores)."""
    teacher = get_teacher_or_redirect(request)
    if teacher is None:
        return redirect("accounts:dashboard")
    exam = get_object_or_404(Exam, pk=exam_id)
    if exam.created_by_id != teacher.pk:
        messages.error(request, "Access denied.")
        return redirect("exams:exam_list")
    exam.result_published = True
    exam.save(update_fields=["result_published"])
    messages.success(request, f"Results for '{exam.title}' are now published.")
    return redirect("exams:exam_attempts_list", exam_id=exam_id)


# ---------- Student exam attempt (no auth required; session stores attempt_id) ----------

SESSION_ATTEMPT_KEY = "exam_attempt_id"


def exam_entry_view(request):
    """Student enters with test code, registration number, DOB. Validate time window, no re-attempt; create attempt."""
    from results.models import StudentAttempt

    if request.method == "POST":
        form = ExamEntryForm(data=request.POST)
        if form.is_valid():
            test_code = form.cleaned_data["test_code"].strip().upper()
            roll_number = form.cleaned_data["registration_number"].strip()
            dob = form.cleaned_data["date_of_birth"]

            exam = Exam.objects.filter(test_code__iexact=test_code).select_related("created_by__college").first()
            if not exam:
                messages.error(request, "Invalid test code.")
                return render(request, "exams/exam_entry.html", {"form": form})

            now = timezone.now()
            if now < exam.start_time:
                messages.error(request, "Exam has not started yet.")
                return render(request, "exams/exam_entry.html", {"form": form})
            if now > exam.end_time:
                messages.error(request, "Exam has ended.")
                return render(request, "exams/exam_entry.html", {"form": form})

            college = exam.created_by.college
            student = college.students.filter(roll_number__iexact=roll_number).first()
            if not student:
                messages.error(request, "Invalid registration number for this exam.")
                return render(request, "exams/exam_entry.html", {"form": form})

            if student.date_of_birth != dob:
                messages.error(request, "Date of birth does not match.")
                return render(request, "exams/exam_entry.html", {"form": form})

            if StudentAttempt.objects.filter(student=student, exam=exam).exists():
                messages.error(request, "You have already attempted this exam.")
                return render(request, "exams/exam_entry.html", {"form": form})

            if exam.questions.count() == 0:
                messages.error(request, "This exam has no questions.")
                return render(request, "exams/exam_entry.html", {"form": form})

            attempt = StudentAttempt.objects.create(student=student, exam=exam)
            request.session[SESSION_ATTEMPT_KEY] = attempt.pk
            messages.success(request, "You can now start the exam.")
            return redirect("exams:attempt_question", attempt_id=attempt.pk, order=1)
        messages.error(request, "Please correct the errors below.")
    else:
        form = ExamEntryForm()

    return render(request, "exams/exam_entry.html", {"form": form})


def get_attempt_for_request(request, attempt_id):
    """Return StudentAttempt if session has this attempt_id; else None."""
    if not attempt_id:
        return None
    session_id = request.session.get(SESSION_ATTEMPT_KEY)
    if session_id != attempt_id:
        return None
    from results.models import StudentAttempt
    return StudentAttempt.objects.filter(pk=attempt_id).select_related("exam", "student").first()


@require_http_methods(["GET", "POST"])
@csrf_protect
def attempt_question_view(request, attempt_id, order):
    """Show one question; sidebar with Attempted / Not Attempted / Marked for Review. Save answer on POST."""
    from results.models import StudentAttempt, StudentAnswer

    attempt = get_attempt_for_request(request, attempt_id)
    if not attempt:
        messages.error(request, "Invalid or expired attempt. Please enter the exam again.")
        return redirect("exams:exam_entry")

    if attempt.submitted_at:
        messages.info(request, "You have already submitted this exam.")
        return redirect("exams:attempt_submitted", attempt_id=attempt_id)

    exam = attempt.exam
    now = timezone.now()
    if now > exam.end_time:
        messages.error(request, "Exam time is over.")
        return redirect("exams:exam_entry")

    questions = list(exam.questions.order_by("order"))
    if not questions:
        return redirect("exams:exam_entry")

    # order is 1-based
    try:
        order = max(1, min(int(order), len(questions)))
    except (TypeError, ValueError):
        order = 1
    question = questions[order - 1]

    # Build sidebar: question_order -> { attempted: bool, marked_for_review: bool }
    answer_map = {a.question_id: a for a in attempt.answers.select_related("question").all()}
    sidebar = []
    for i, q in enumerate(questions):
        o = i + 1
        a = answer_map.get(q.id)
        sidebar.append({
            "order": o,
            "attempted": bool(a and a.selected_option),
            "marked_for_review": bool(a and a.marked_for_review),
        })

    if request.method == "POST":
        selected = request.POST.get("selected_option", "").strip()
        if selected in ("A", "B", "C", "D"):
            pass
        else:
            selected = ""
        mark_for_review = request.POST.get("marked_for_review") == "1"
        next_order = request.POST.get("next_order")  # "next", "prev", or number

        obj, _ = StudentAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={"selected_option": selected, "marked_for_review": mark_for_review},
        )

        # Redirect to next/prev/question
        if next_order == "next":
            go = order + 1 if order < len(questions) else order
        elif next_order == "prev":
            go = order - 1 if order > 1 else 1
        else:
            try:
                go = max(1, min(int(next_order), len(questions)))
            except (TypeError, ValueError):
                go = order
        return redirect("exams:attempt_question", attempt_id=attempt_id, order=go)

    # Current answer
    current_answer = answer_map.get(question.id)
    selected_option = current_answer.selected_option if current_answer else ""
    marked_for_review = bool(current_answer and current_answer.marked_for_review)

    # Timer: end at min(exam.end_time, started_at + duration)
    from datetime import timedelta
    end_at = min(
        exam.end_time,
        attempt.started_at + timedelta(minutes=exam.duration_minutes),
    )
    duration_seconds = max(0, int((end_at - timezone.now()).total_seconds()))

    sidebar_review_orders = [s["order"] for s in sidebar if s["marked_for_review"]]
    context = {
        "attempt": attempt,
        "exam": exam,
        "question": question,
        "questions": questions,
        "order": order,
        "sidebar": sidebar,
        "sidebar_review_orders": sidebar_review_orders,
        "selected_option": selected_option,
        "marked_for_review": marked_for_review,
        "duration_seconds": duration_seconds,
        "submit_url": reverse_lazy_attempt_submit(attempt_id),
    }
    return render(request, "exams/attempt_question.html", context)


def reverse_lazy_attempt_submit(attempt_id):
    from django.urls import reverse
    return reverse("exams:attempt_submit", kwargs={"attempt_id": attempt_id})


@require_http_methods(["GET", "POST"])
@csrf_protect
def attempt_submit_view(request, attempt_id):
    """Mark attempt as submitted; compute and store score in one atomic transaction; clear session."""
    from results.models import StudentAttempt
    from results.evaluation import compute_attempt_score

    attempt = get_attempt_for_request(request, attempt_id)
    if not attempt:
        messages.error(request, "Invalid or expired attempt.")
        return redirect("exams:exam_entry")

    if request.method == "POST":
        try:
            with transaction.atomic():
                total_score, max_score = compute_attempt_score(attempt)
                attempt.submitted_at = timezone.now()
                attempt.total_score = total_score
                attempt.max_score = max_score
                attempt.save(update_fields=["submitted_at", "total_score", "max_score"])
        except Exception as e:
            messages.error(request, f"Could not submit: {str(e)}")
            return redirect("exams:attempt_submit", attempt_id=attempt_id)
        if request.session.get(SESSION_ATTEMPT_KEY) == attempt_id:
            del request.session[SESSION_ATTEMPT_KEY]
        messages.success(request, "Your exam has been submitted successfully.")
        return redirect("exams:attempt_submitted", attempt_id=attempt_id)

    # GET: show confirm submit page, or submitted thank you
    if attempt.submitted_at:
        return render(request, "exams/attempt_submitted.html", {"attempt": attempt})
    return render(request, "exams/attempt_confirm_submit.html", {"attempt": attempt, "exam": attempt.exam})


def attempt_submitted_view(request, attempt_id):
    """Thank you / already submitted page."""
    attempt = get_attempt_for_request(request, attempt_id)
    if not attempt:
        # Allow viewing thank you even if session cleared after submit
        from results.models import StudentAttempt
        attempt = StudentAttempt.objects.filter(pk=attempt_id).first()
    return render(request, "exams/attempt_submitted.html", {"attempt": attempt})
