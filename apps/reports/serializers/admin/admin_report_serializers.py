from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.core.choices import ReportActionType, ReportStatus, TargetType


class AdminReportListQuerySerializer(serializers.Serializer[dict[str, Any]]):
    status = serializers.ChoiceField(
        choices=[
            ReportStatus.PENDING.upper(),
            ReportStatus.HANDLED.upper(),
            ReportStatus.DISMISSED.upper(),
        ],
        required=False,
    )
    target_type = serializers.ChoiceField(
        choices=[
            TargetType.POST.upper(),
            TargetType.COMMENT.upper(),
        ],
        required=False,
    )
    page = serializers.IntegerField(min_value=1)
    size = serializers.IntegerField(min_value=1)


class AdminReportTargetPreviewSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    title = serializers.CharField(required=False)
    content = serializers.CharField(required=False)
    status = serializers.CharField(required=False)


class AdminReportListItemSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    admin_id = serializers.IntegerField(allow_null=True)
    target_id = serializers.IntegerField()
    target_type = serializers.CharField()
    target_preview = AdminReportTargetPreviewSerializer()
    reason_type = serializers.CharField()
    reason_detail = serializers.CharField(allow_null=True, allow_blank=True)
    status = serializers.CharField()
    action_type = serializers.CharField(allow_null=True, required=False)
    memo = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    handled_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class AdminReportListSuccessResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = AdminReportListItemSerializer(many=True)


class AdminReportActionRequestSerializer(serializers.Serializer[dict[str, Any]]):
    action_type = serializers.ChoiceField(
        choices=[
            ReportActionType.DELETE.upper(),
            ReportActionType.KEEP.upper(),
        ]
    )
    memo = serializers.CharField(required=False, allow_blank=True, max_length=1000)
