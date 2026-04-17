from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.core.choices import ReportReasonType


class PostReportCreateSerializer(serializers.Serializer[Any]):
    reason_type = serializers.ChoiceField(
        required=True,
        choices=ReportReasonType.choices,
        error_messages={"reason_type": "올바른 신고 유형을 선택해주세요."},
    )
    reason_detail = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["reason_type"] == ReportReasonType.OTHER and not attrs.get("reason_detail"):
            raise serializers.ValidationError({"reason_detail": ["기타의 경우 상세 사유가 필요합니다."]})

        return attrs


class PostReportCreateResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()
    report_id = serializers.IntegerField()
