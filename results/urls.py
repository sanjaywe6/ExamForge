from django.urls import path

from . import views

app_name = "results"

urlpatterns = [
    path("", views.my_results_list_view, name="my_results_list"),
    path("<int:attempt_id>/", views.my_result_detail_view, name="my_result_detail"),
]
