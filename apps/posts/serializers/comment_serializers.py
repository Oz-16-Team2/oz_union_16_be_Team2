from typing import Any

from rest_framework import serializers

from apps.posts.models import Comment
from apps.users.constants import PROFILE_IMAGE_URL_MAP


class CommentCreateSerializer(serializers.ModelSerializer[Any]):
    """
    REQ-COMM-001: 댓글 작성 API 시리얼라이저
    """

    # 응답 시에만 보여줄 필드들 (read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    nickname = serializers.CharField(source="user.nickname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user_id", "nickname", "content", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_content(self, value: str) -> str:
        """댓글 내용 길이 검증"""
        if len(value) > 500:
            raise serializers.ValidationError(
                "최대 500자까지 입력 가능합니다."
            )  # 400 은 시리얼라이저, 404나 409는 뷰에서
        return value


class CommentListSerializer(serializers.ModelSerializer[Any]):
    """
    REQ-COMM-002: 댓글 목록 조회 API 시리얼라이저
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    nickname = serializers.CharField(source="user.nickname", read_only=True)
    profile_image_url = serializers.SerializerMethodField()

    # 뷰(View)에서 annotate로 계산해서 넘겨줄 필드들
    like_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user_id", "nickname", "content", "created_at", "like_count", "is_liked", "profile_image_url"]

    def get_profile_image_url(self, obj: Comment) -> str | None:
        for social in obj.user.social_logins.all():
            if social.social_profile_image_url:
                return social.social_profile_image_url
        return PROFILE_IMAGE_URL_MAP.get(obj.user.profile_image)


class CommentReportSerializer(serializers.Serializer[Any]):
    """
    REQ-COMM-005: 댓글 신고 API 시리얼라이저
    """

    reason = serializers.CharField(required=True, help_text="신고 사유")
