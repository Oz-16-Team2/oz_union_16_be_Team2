from django.urls import path

from apps.reports.views.admin.admin_report_views import (
    AdminReportActionAPIView,
    AdminReportListAPIView,
)

urlpatterns = [
    path("reports", AdminReportListAPIView.as_view(), name="admin-report-list"),
    path("reports/<int:report_id>/actions", AdminReportActionAPIView.as_view(), name="admin-report-action"),
]
