from django.urls import path

from . import views
app_name = "exams"

urlpatterns = [
    path("", views.exam_list_view, name="exam_list"),
    path("create/", views.exam_create_view, name="exam_create"),
    path("<int:exam_id>/", views.exam_detail_view, name="exam_detail"),
    path("<int:exam_id>/upload-questions/", views.exam_upload_questions_view, name="exam_upload_questions"),
    path("<int:exam_id>/attempts/", views.exam_attempts_list_view, name="exam_attempts_list"),
    path("<int:exam_id>/publish-results/", views.exam_publish_results_view, name="exam_publish_results"),
    path("<int:exam_id>/toggle-publish/", views.exam_toggle_publish_view, name="exam_toggle_publish"),
    # Student attempt (no login; session-based)
    path("student/", views.student_exams_view, name="student_exams"),
    path("<int:exam_id>/info/", views.exam_info_view, name="exam_info"),
    path("attempt/<int:attempt_id>/q/<int:order>/", views.attempt_question_view, name="attempt_question"),
    path("attempt/<int:attempt_id>/submit/", views.attempt_submit_view, name="attempt_submit"),
    path("attempt/<int:attempt_id>/submitted/", views.attempt_submitted_view, name="attempt_submitted"),
]
from django.urls import path

from . import views

app_name = "exams"

urlpatterns = [
    path("", views.exam_list_view, name="exam_list"),
    path("create/", views.exam_create_view, name="exam_create"),
    path("<int:exam_id>/", views.exam_detail_view, name="exam_detail"),
    path("<int:exam_id>/upload-questions/", views.exam_upload_questions_view, name="exam_upload_questions"),
    path("<int:exam_id>/attempts/", views.exam_attempts_list_view, name="exam_attempts_list"),
    path("<int:exam_id>/publish-results/", views.exam_publish_results_view, name="exam_publish_results"),
    path("<int:exam_id>/toggle-publish/", views.exam_toggle_publish_view, name="exam_toggle_publish"),
    # Student attempt (no login; session-based)
    path("enter/", views.exam_entry_view, name="exam_entry"),
    path("student/", views.student_exams_view, name="student_exams"),
    path("<int:exam_id>/info/", views.exam_info_view, name="exam_info"),
    path("attempt/<int:attempt_id>/q/<int:order>/", views.attempt_question_view, name="attempt_question"),
    path("attempt/<int:attempt_id>/submit/", views.attempt_submit_view, name="attempt_submit"),
    path("attempt/<int:attempt_id>/submitted/", views.attempt_submitted_view, name="attempt_submitted"),
]
