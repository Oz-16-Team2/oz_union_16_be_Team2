from typing import Any

from rest_framework import serializers

from apps.posts.models import Comment
from apps.users.utils import get_user_display_info


class CommentCreateSerializer(serializers.ModelSerializer[Any]):
    """
    REQ-COMM-001: 댓글 작성 API 시리얼라이저
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)

    nickname = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "user_id", "nickname", "content", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_nickname(self, obj: Comment) -> str:
        nickname, _ = get_user_display_info(obj.user)
        return nickname

    def validate_content(self, value: str) -> str:
        if len(value) > 500:
            raise serializers.ValidationError("최대 500자까지 입력 가능합니다.")
        return value


class CommentListSerializer(serializers.ModelSerializer[Any]):
    """
    REQ-COMM-002: 댓글 목록 조회 API 시리얼라이저
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)

    nickname = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()

    like_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user_id", "nickname", "content", "created_at", "like_count", "is_liked", "profile_image_url"]

    def get_nickname(self, obj: Comment) -> str:
        nickname, _ = get_user_display_info(obj.user)
        return nickname

    def get_profile_image_url(self, obj: Comment) -> str | None:
        _, profile_url = get_user_display_info(obj.user)
        return profile_url


class CommentReportSerializer(serializers.Serializer[Any]):
    """
    REQ-COMM-005: 댓글 신고 API 시리얼라이저
    """

    reason = serializers.CharField(required=True, help_text="신고 사유")
