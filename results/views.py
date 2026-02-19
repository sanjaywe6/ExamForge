"""
Student results: view only when exam.result_published. Teachers use exams app for attempts/publish.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.models import CustomUser


@login_required(login_url="accounts:login")
def my_results_list_view(request):
    """Student: list my attempts; show score only if result_published."""
    if request.user.role != CustomUser.Role.STUDENT:
        messages.error(request, "Access denied.")
        return redirect("accounts:dashboard")
    try:
        student = request.user.student_profile
    except Exception:
        messages.error(request, "Student profile not found.")
        return redirect("accounts:dashboard")

    from .models import StudentAttempt
    attempts = (
        StudentAttempt.objects.filter(student=student)
        .select_related("exam")
        .order_by("-submitted_at")
    )
    return render(request, "results/my_results_list.html", {"attempts": attempts})


@login_required(login_url="accounts:login")
def my_result_detail_view(request, attempt_id):
    """Student: view one attempt result; 403 if not published or not own attempt."""
    if request.user.role != CustomUser.Role.STUDENT:
        messages.error(request, "Access denied.")
        return redirect("accounts:dashboard")
    try:
        student = request.user.student_profile
    except Exception:
        messages.error(request, "Student profile not found.")
        return redirect("accounts:dashboard")

    from .models import StudentAttempt
    attempt = get_object_or_404(StudentAttempt, pk=attempt_id)
    if attempt.student_id != student.pk:
        messages.error(request, "You can only view your own results.")
        return redirect("results:my_results_list")
    if not attempt.exam.result_published:
        messages.error(request, "Results for this exam are not published yet.")
        return redirect("results:my_results_list")
    # Show stored total_score/max_score only (no recompute; prevent tampering)
    return render(
        request,
        "results/my_result_detail.html",
        {"attempt": attempt, "exam": attempt.exam},
    )
