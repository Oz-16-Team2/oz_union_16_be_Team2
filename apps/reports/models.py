from django.db import models

from apps.core.choices import ReportReasonType, ReportStatus, TargetType
from apps.users.models import User


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="handled_reports")
    target_id = models.BigIntegerField()
    target_type = models.CharField(max_length=10, choices=TargetType.choices)
    reason_type = models.CharField(max_length=100, choices=ReportReasonType.choices)
    reason_detail = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    handled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reports"


class ReportAction(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="actions")
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="report_actions")
    action_type = models.CharField(max_length=30)
    memo = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "report_actions"
