from django.urls import path

from . import views

app_name = "colleges"

urlpatterns = [
    path("register-teacher/", views.register_teacher_view, name="register_teacher"),
    path("students/import/", views.import_students_view, name="import_students"),
    path("students/manage/", views.manage_students_view, name="manage_students"),
    path("students/<int:student_id>/edit/", views.edit_student_view, name="edit_student"),
]
