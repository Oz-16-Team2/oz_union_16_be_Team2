from django.db import models

from apps.core.choices import ReportActionType, ReportReasonType, ReportStatus, TargetType
from apps.users.models import User


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="handled_reports")
    target_id = models.BigIntegerField(help_text="신고 대상의 ID")
    target_type = models.CharField(max_length=20, choices=TargetType.choices, help_text="신고 대상의 유형")
    reason_type = models.CharField(max_length=100, choices=ReportReasonType.choices, help_text="신고 사유")
    reason_detail = models.TextField(max_length=500, null=True, blank=True, help_text="신고 사유 상세 설명")
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING,
        help_text="신고의 처리 상태",
    )
    handled_at = models.DateTimeField(null=True, blank=True, help_text="신고의 처리 일시")
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정일")

    class Meta:
        db_table = "reports"
        verbose_name = "신고"
        verbose_name_plural = "신고 목록"


class ReportAction(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="신고ID")
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="처리한관리자ID")
    action_type = models.CharField(
        max_length=50,
        choices=ReportActionType.choices,
    )
    memo = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text="신고의 처리 일시")

    class Meta:
        db_table = "report_actions"
        verbose_name = "신고 처리 이력"
        verbose_name_plural = "신고 처리 이력 목록"
