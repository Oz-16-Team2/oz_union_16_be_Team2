from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.core.choices import CommentStatus, PostStatus


class AdminPostTagSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    name = serializers.CharField()


class AdminPostListQuerySerializer(serializers.Serializer[dict[str, Any]]):
    users_id = serializers.IntegerField(required=False, min_value=1)
    status = serializers.ChoiceField(
        choices=[
            PostStatus.ACTIVE.upper(),
            PostStatus.DELETED.upper(),
            PostStatus.REPORTED.upper(),
        ],
        required=False,
    )
    has_goal = serializers.BooleanField(required=False)
    has_vote = serializers.BooleanField(required=False)
    page = serializers.IntegerField(min_value=1)
    size = serializers.IntegerField(min_value=1)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        for field in ("has_goal", "has_vote"):
            if field not in self.initial_data:
                attrs.pop(field, None)
        return attrs


class AdminPostListItemSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    users_id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_image_url = serializers.URLField(allow_null=True, allow_blank=True)
    title = serializers.CharField()
    content = serializers.CharField()
    image_url = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    has_goal = serializers.BooleanField()
    has_vote = serializers.BooleanField()
    tags = AdminPostTagSerializer(many=True)
    like_count = serializers.IntegerField()
    scrap_count = serializers.IntegerField()
    report_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    deleted_at = serializers.DateTimeField(allow_null=True)


class AdminPostListSuccessResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = AdminPostListItemSerializer(many=True)


class AdminPostDetailCommentSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    nickname = serializers.CharField()
    content = serializers.CharField()
    status = serializers.ChoiceField(
        choices=[
            CommentStatus.ACTIVE.upper(),
            CommentStatus.DELETED.upper(),
        ]
    )
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class AdminPostDetailVoteOptionSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    content = serializers.CharField()
    sort_order = serializers.IntegerField()


class AdminPostDetailVoteSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    question = serializers.CharField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    status = serializers.CharField()
    options = AdminPostDetailVoteOptionSerializer(many=True)


class AdminPostDetailItemSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    users_id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_image_url = serializers.URLField(allow_null=True, allow_blank=True)
    goals_id = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    content = serializers.CharField()
    status = serializers.CharField()
    images = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
    )
    tags = AdminPostTagSerializer(many=True)
    goal_start_date = serializers.DateTimeField(allow_null=True)
    goal_end_date = serializers.DateTimeField(allow_null=True)
    goal_title = serializers.CharField(allow_null=True)
    goal_progress = serializers.IntegerField(allow_null=True)
    like_count = serializers.IntegerField()
    scrap_count = serializers.IntegerField()
    comments = AdminPostDetailCommentSerializer(many=True)
    vote = AdminPostDetailVoteSerializer(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    deleted_at = serializers.DateTimeField(allow_null=True)


class AdminPostDetailSuccessResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = AdminPostDetailItemSerializer()


class AdminPostStatusUpdateRequestSerializer(serializers.Serializer[dict[str, Any]]):
    status = serializers.ChoiceField(
        choices=[
            PostStatus.ACTIVE.upper(),
            PostStatus.REPORTED.upper(),
        ]
    )
