# apps/users/serializers/admin/admin_user_serializers.py

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.core.choices import UserStatus


class AdminUserListQuerySerializer(serializers.Serializer[dict[str, Any]]):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    size = serializers.IntegerField(min_value=1, required=False, default=10)
    status = serializers.ChoiceField(
        choices=[
            UserStatus.ACTIVE.upper(),
            UserStatus.SUSPENDED.upper(),
            UserStatus.RESTRICTED.upper(),
        ],
        required=False,
    )


class AdminUserListItemSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    nickname = serializers.CharField()
    profile_image_url = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    status_expires_at = serializers.DateTimeField(allow_null=True)
    memo = serializers.CharField(allow_null=True, allow_blank=True)

    total_goals_count = serializers.IntegerField()
    post_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    post_report_count = serializers.IntegerField()
    comment_report_count = serializers.IntegerField()

    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    deleted_at = serializers.DateTimeField(allow_null=True)


class AdminUserListSuccessResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = AdminUserListItemSerializer(many=True)


class AdminUserStatusUpdateRequestSerializer(serializers.Serializer[dict[str, Any]]):
    status = serializers.ChoiceField(
        choices=[
            UserStatus.ACTIVE.upper(),
            UserStatus.SUSPENDED.upper(),
            UserStatus.RESTRICTED.upper(),
        ]
    )
    status_expires_at = serializers.DateTimeField(required=False, allow_null=True)
    memo = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=1000)
