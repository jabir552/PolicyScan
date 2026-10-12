from django.urls import path
from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path("scan/", views.run_scan_view, name="run_scan"),
    path("report/<int:report_id>/", views.report_detail_view, name="report_detail"),
    path("report/<int:report_id>/csv/", views.export_csv_view, name="export_csv"),
    path("history/", views.history_view, name="history"),
    path("samples/", views.demo_sample_view, name="demo_sample"),
]
