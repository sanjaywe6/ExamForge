from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("login/student/", views.login_student_view, name="login_student"),
    path("login/teacher/", views.login_teacher_view, name="login_teacher"),
    path("login/college/", views.login_college_view, name="login_college"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/college-admin/", views.dashboard_college_admin_view, name="dashboard_college_admin"),
    path("dashboard/teacher/", views.dashboard_teacher_view, name="dashboard_teacher"),
    path("dashboard/student/", views.dashboard_student_view, name="dashboard_student"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
]
