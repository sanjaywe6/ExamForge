from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/college-admin/", views.dashboard_college_admin_view, name="dashboard_college_admin"),
    path("dashboard/teacher/", views.dashboard_teacher_view, name="dashboard_teacher"),
    path("dashboard/student/", views.dashboard_student_view, name="dashboard_student"),
]
