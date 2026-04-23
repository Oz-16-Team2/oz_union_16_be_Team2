from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.core.common_serializers import KSTDateTimeField


class AdminUserListQuerySerializer(serializers.Serializer[dict[str, Any]]):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    size = serializers.IntegerField(min_value=1, required=False, default=10)
    status = serializers.ChoiceField(
        choices=["ACTIVE", "SUSPENDED"],
        required=False,
    )

    def validate_status(self, value: str) -> str:
        return value.upper()


class AdminUserListItemSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    nickname = serializers.CharField()
    profile_image_url = serializers.CharField(allow_null=True, allow_blank=True)

    total_goals_count = serializers.IntegerField()
    post_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    post_report_count = serializers.IntegerField()
    comment_report_count = serializers.IntegerField()

    status = serializers.ChoiceField(choices=["ACTIVE", "SUSPENDED"])
    memo = serializers.CharField(allow_null=True, allow_blank=True)
    status_expires_at = KSTDateTimeField(allow_null=True)

    created_at = KSTDateTimeField()
    updated_at = KSTDateTimeField()
    deleted_at = KSTDateTimeField(allow_null=True)


class AdminUserListSuccessResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = AdminUserListItemSerializer(many=True)


class AdminUserStatusUpdateRequestSerializer(serializers.Serializer[dict[str, Any]]):
    status = serializers.ChoiceField(
        choices=["ACTIVE", "SUSPENDED"],
    )
    status_expires_at = KSTDateTimeField(required=False, allow_null=True)
    memo = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=1000)

    def validate_status(self, value: str) -> str:
        return value.upper()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        status = attrs["status"]

        if status == "SUSPENDED" and not attrs.get("status_expires_at"):
            raise serializers.ValidationError("정지 상태는 만료 시간이 필요합니다.")

        return attrs
