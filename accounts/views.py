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


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            messages.success(request, "You are now logged in.")
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("accounts:dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm(request=request)
    return render(request, "accounts/login.html", {"form": form})


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
    return render(
        request,
        "accounts/dashboard_college_admin.html",
        {"college": college},
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
        college = None
    return render(
        request,
        "accounts/dashboard_teacher.html",
        {"college": college},
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
        college = None
    return render(
        request,
        "accounts/dashboard_student.html",
        {"college": college},
    )
