"""
Session-based authentication: login, logout, College Admin registration, role-based dashboards.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .models import CustomUser
from .forms import LoginForm, CollegeAdminRegistrationForm
from .forms import ProfileEditForm


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            messages.success(request, "You are now logged in.")
            # If student selected student login, redirect them to student dashboard
            account_type = form.cleaned_data.get("account_type")
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                return redirect(next_url)
            if account_type == 'student':
                return redirect("accounts:dashboard_student")
            return redirect("accounts:dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm(request=request)
    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_student_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    template = "accounts/login_student.html"
    if request.method == "POST":
        data = request.POST.copy()
        data["account_type"] = "student"
        form = LoginForm(request=request, data=data)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect("accounts:dashboard_student")
        messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm(request=request, initial={"account_type": "student"})
    return render(request, template, {"form": form})


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_teacher_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    template = "accounts/login_teacher.html"
    if request.method == "POST":
        data = request.POST.copy()
        data["account_type"] = "staff"
        form = LoginForm(request=request, data=data)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect("accounts:dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm(request=request, initial={"account_type": "staff"})
    return render(request, template, {"form": form})


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_college_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    template = "accounts/login_college.html"
    if request.method == "POST":
        data = request.POST.copy()
        data["account_type"] = "staff"
        form = LoginForm(request=request, data=data)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect("accounts:dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm(request=request, initial={"account_type": "staff"})
    return render(request, template, {"form": form})


@require_http_methods(["POST"])
@csrf_protect
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


@require_http_methods(["GET", "POST"])
@csrf_protect
def register_view(request):
    """Registration only for College Admin. Creates College + User + CollegeAdmin."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = CollegeAdminRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. You can log in now.")
            return redirect("accounts:login")
        messages.error(request, "Please correct the errors below.")
    else:
        form = CollegeAdminRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required(login_url="accounts:login")
def dashboard_view(request):
    """Role-based redirect to the correct dashboard."""
    user = request.user
    if user.role == CustomUser.Role.COLLEGE_ADMIN:
        return redirect("accounts:dashboard_college_admin")
    if user.role == CustomUser.Role.TEACHER:
        return redirect("accounts:dashboard_teacher")
    if user.role == CustomUser.Role.STUDENT:
        return redirect("accounts:dashboard_student")
    messages.warning(request, "Unknown role.")
    return redirect("accounts:login")


@login_required(login_url="accounts:login")
def dashboard_college_admin_view(request):
    if request.user.role != CustomUser.Role.COLLEGE_ADMIN:
        messages.error(request, "Access denied.")
        return redirect("accounts:dashboard")
    try:
        profile = request.user.college_admin_profile
        college = profile.college
    except Exception:
        college = None
    stats = {}
    recent_teachers = []
    recent_batches = []
    if college:
        from exams.models import Exam
        stats["teachers_count"] = college.teachers.count()
        stats["students_count"] = college.students.count()
        stats["exams_count"] = Exam.objects.filter(created_by__college=college).count()
        recent_teachers = college.teachers.select_related("user").order_by("-created_at")[:5]
        recent_batches = college.student_batches.prefetch_related("students").order_by("-created_at")[:5]
    else:
        stats = {"teachers_count": 0, "students_count": 0, "exams_count": 0}
    return render(
        request,
        "accounts/dashboard_college_admin.html",
        {"college": college, "stats": stats, "recent_teachers": recent_teachers, "recent_batches": recent_batches},
    )


@login_required(login_url="accounts:login")
def dashboard_teacher_view(request):
    if request.user.role != CustomUser.Role.TEACHER:
        messages.error(request, "Access denied.")
        return redirect("accounts:dashboard")
    try:
        profile = request.user.teacher_profile
        college = profile.college
    except Exception:
        profile = None
        college = None
    from exams.models import Exam
    from results.models import StudentAttempt
    if profile:
        exams = Exam.objects.filter(created_by=profile).order_by("-start_time")[:10]
        exams_count = Exam.objects.filter(created_by=profile).count()
        attempts_count = StudentAttempt.objects.filter(exam__created_by=profile).count()
    else:
        exams = []
        exams_count = attempts_count = 0
    return render(
        request,
        "accounts/dashboard_teacher.html",
        {"college": college, "exams": exams, "exams_count": exams_count, "attempts_count": attempts_count},
    )


@login_required(login_url="accounts:login")
def dashboard_student_view(request):
    if request.user.role != CustomUser.Role.STUDENT:
        messages.error(request, "Access denied.")
        return redirect("accounts:dashboard")
    try:
        profile = request.user.student_profile
        college = profile.college
    except Exception:
        profile = None
        college = None
    from results.models import StudentAttempt
    if profile:
        attempts = StudentAttempt.objects.filter(student=profile).select_related("exam").order_by("-submitted_at")[:10]
        attempts_count = StudentAttempt.objects.filter(student=profile).count()
    else:
        attempts = []
        attempts_count = 0
    return render(
        request,
        "accounts/dashboard_student.html",
        {"college": college, "attempts": attempts, "attempts_count": attempts_count},
    )


@login_required(login_url="accounts:login")
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(user=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})
