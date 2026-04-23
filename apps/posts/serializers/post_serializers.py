from __future__ import annotations

from datetime import datetime, time
from typing import Any

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from apps.core.choices import CommentStatus
from apps.goals.models import Goal
from apps.posts.models import Post, PostTag, Tag

MAX_TAGS = 3
CONTENT_PREVIEW_LENGTH = 100

SCOPE_FEED = "FEED"
SCOPE_MY = "MY"
SORT_LATEST = "LATEST"
SORT_POPULAR = "POPULAR"


class PostListQuerySerializer(serializers.Serializer[Any]):
    scope = serializers.ChoiceField(
        choices=[SCOPE_FEED, SCOPE_MY],
        required=False,
        default=SCOPE_FEED,
        error_messages={"invalid_choice": "조회 범위가 올바르지 않습니다."},
    )
    sort_by = serializers.ChoiceField(
        choices=[SORT_LATEST, SORT_POPULAR],
        required=False,
        default=SORT_LATEST,
        error_messages={"invalid_choice": "정렬 기준이 올바르지 않습니다."},
    )
    page = serializers.IntegerField(required=False, min_value=0, default=0)
    size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class PostSearchQuerySerializer(serializers.Serializer[Any]):
    keyword = serializers.CharField(
        min_length=2, error_messages={"min_length": "검색어는 최소 2글자 이상 입력해야 합니다."}
    )
    type = serializers.ChoiceField(choices=["title", "content"], required=False)
    page = serializers.IntegerField(required=False, min_value=0, default=0)
    size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class PostFeedItemSerializer(serializers.Serializer[Any]):
    post_id = serializers.IntegerField()
    images = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    profile_image_url = serializers.CharField(max_length=255, allow_null=True, required=False, allow_blank=True)
    nickname = serializers.CharField()
    created_at = serializers.DateTimeField()
    title = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    content_preview = serializers.CharField()
    like_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    is_scrapped = serializers.BooleanField()


class PostSearchResponseSerializer(serializers.Serializer[Any]):
    search_results = PostFeedItemSerializer(many=True)
    keyword = serializers.CharField()
    total_count = serializers.IntegerField()
    sort_by = serializers.ChoiceField(
        choices=[SORT_LATEST, SORT_POPULAR],
        required=False,
        default=SORT_LATEST,
        error_messages={"invalid_choice": "정렬 기준이 올바르지 않습니다."},
    )
    page = serializers.IntegerField(
        required=False,
        min_value=0,
        default=0,
    )
    size = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        default=20,
    )


class VoteOptionWriteSerializer(serializers.Serializer[Any]):
    content = serializers.CharField(max_length=255)
    sort_order = serializers.IntegerField(min_value=0)


class VoteWriteSerializer(serializers.Serializer[Any]):
    question = serializers.CharField(max_length=255)
    options = VoteOptionWriteSerializer(many=True)


class PostCreateSerializer(serializers.Serializer[Any]):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    images = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)
    is_private = serializers.BooleanField(
        required=False,
        default=False,
    )
    has_goal = serializers.BooleanField()
    goal_id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
    has_vote = serializers.BooleanField()
    vote = VoteWriteSerializer(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=list,
    )

    def validate_title(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("제목은 필수 입력 사항입니다.")
        return value

    def validate_content(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("내용은 필수 입력 사항입니다.")
        return value

    def validate_images(self, value: list[str]) -> list[str]:
        if len(value) > 3:
            raise serializers.ValidationError("이미지는 최대 3개까지만 등록 가능합니다.")
        return value

    def validate_tag_ids(self, value: list[int]) -> list[int]:
        if len(value) > MAX_TAGS:
            raise serializers.ValidationError("태그는 최대 3개까지만 등록 가능합니다.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("has_goal") and not attrs.get("goal_id"):
            raise serializers.ValidationError({"goal_id": ["목표가 있을 경우 goal_id가 필요합니다."]})

        if attrs.get("has_vote"):
            vote = attrs.get("vote")
            if not vote or not vote.get("question"):
                raise serializers.ValidationError(
                    {"vote": ["투표의 질문과 선택지가 필요합니다."]},
                )
            options = vote.get("options") or []
            if len(options) < 2:
                raise serializers.ValidationError({"vote": ["2개 이상의 선택지가 필요합니다."]})
        else:
            attrs["vote"] = None

        return attrs


class PostCreateResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()
    post_id = serializers.IntegerField()


class PostPatchSerializer(serializers.Serializer[Any]):
    title = serializers.CharField(max_length=255, required=False, allow_blank=False)
    content = serializers.CharField(required=False)
    images = serializers.ListField(child=serializers.CharField(max_length=500), required=False)
    is_private = serializers.BooleanField(required=False)
    has_goal = serializers.BooleanField(required=False)
    goal_id = serializers.IntegerField(required=False, allow_null=True)
    has_vote = serializers.BooleanField(required=False)
    vote = VoteWriteSerializer(required=False, allow_null=True)
    is_vote_closed = serializers.BooleanField(required=False, default=False)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
    )

    def validate_images(self, value: list[str]) -> list[str]:
        if len(value) > 3:
            raise serializers.ValidationError("이미지는 최대 3개까지만 등록 가능합니다.")
        return value

    def validate_tag_ids(self, value: list[int]) -> list[int]:
        if len(value) > MAX_TAGS:
            raise serializers.ValidationError("태그는 최대 3개까지만 등록 가능합니다.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:

        if attrs.get("has_goal") and not attrs.get("goal_id"):
            raise serializers.ValidationError({"goal_id": ["목표가 있을 경우 goal_id가 필요합니다."]})

        if attrs.get("has_vote"):
            vote = attrs.get("vote")
            if not vote or not vote.get("question"):
                raise serializers.ValidationError(
                    {"vote": ["투표의 질문과 선택지가 필요합니다."]},
                )
            options = vote.get("options") or []
            if len(options) < 2:
                raise serializers.ValidationError({"vote": ["2개 이상의 선택지가 필요합니다."]})

        return attrs


class MessageDetailSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()


class VoteOptionDetailSerializer(serializers.Serializer[Any]):
    option_id = serializers.IntegerField()
    content = serializers.CharField()
    sort_order = serializers.IntegerField()


class VoteInfoSerializer(serializers.Serializer[Any]):
    vote_id = serializers.IntegerField()
    question = serializers.CharField(max_length=255)
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    status = serializers.CharField()
    options = VoteOptionDetailSerializer(many=True)


class GoalInfoSerializer(serializers.Serializer[Any]):
    goal_id = serializers.IntegerField()
    goal_title = serializers.CharField()
    goal_start_date = serializers.DateTimeField(allow_null=True)
    goal_end_date = serializers.DateTimeField(allow_null=True)
    goal_progress = serializers.IntegerField(allow_null=True)


class PostFeedResponseSerializer(serializers.Serializer[Any]):
    posts = PostFeedItemSerializer(many=True)
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total_count = serializers.IntegerField()


class PostSuggestionItemSerializer(serializers.Serializer[Any]):
    post_id = serializers.IntegerField()
    images = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    profile_image_url = serializers.CharField(allow_null=True, required=False, allow_blank=True)
    nickname = serializers.CharField()
    created_at = serializers.DateTimeField()
    title = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    content_preview = serializers.CharField()
    like_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    is_scrapped = serializers.BooleanField()


class PostSuggestionResponseSerializer(serializers.Serializer[Any]):
    posts = PostSuggestionItemSerializer(many=True)
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total_count = serializers.IntegerField()


class PostDetailSerializer(serializers.Serializer[Any]):
    post_id = serializers.IntegerField()
    images = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    profile_image_url = serializers.CharField(allow_null=True, required=False, allow_blank=True)
    nickname = serializers.CharField()
    created_at = serializers.DateTimeField()
    title = serializers.CharField()
    content = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    like_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    is_scrapped = serializers.BooleanField()
    has_goal = serializers.BooleanField()
    goal_info = GoalInfoSerializer(allow_null=True, required=False)
    has_vote = serializers.BooleanField()
    vote_info = VoteInfoSerializer(allow_null=True, required=False)


def build_feed_item(
    post: Post,
    *,
    tags: list[str],
    like_count: int,
    comment_count: int,
    is_scrapped: bool,
) -> dict[str, Any]:
    preview = post.content[:CONTENT_PREVIEW_LENGTH] if post.content else ""
    return {
        "post_id": post.id,
        "images": post.images or [],
        "profile_image_url": (
            f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{post.user.profile_image}"
            if post.user.profile_image
            else None
        ),
        "nickname": post.user.nickname,
        "created_at": post.created_at,
        "title": post.title,
        "tags": tags,
        "content_preview": preview,
        "like_count": like_count,
        "comment_count": comment_count,
        "is_scrapped": is_scrapped,
    }


def build_post_detail(
    post: Post,
    *,
    tags: list[str],
    like_count: int,
    comment_count: int,
    is_scrapped: bool,
    vote_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    has_goal = post.goal_id is not None
    goal_info = None
    if has_goal:
        goal_info = {
            "goal_id": post.goal_id,
            "goal_title": post.goal_title or "",
            "goal_start_date": post.goal_start_date,
            "goal_end_date": post.goal_end_date,
            "goal_progress": post.goal_progress,
        }
    has_vote = vote_payload is not None
    return {
        "post_id": post.id,
        "images": post.images or [],
        "profile_image_url": (
            f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{post.user.profile_image}"
            if post.user.profile_image
            else None
        ),
        "nickname": post.user.nickname,
        "created_at": post.created_at,
        "title": post.title,
        "content": post.content,
        "tags": tags,
        "like_count": like_count,
        "comment_count": comment_count,
        "is_scrapped": is_scrapped,
        "has_goal": has_goal,
        "goal_info": goal_info,
        "has_vote": has_vote,
        "vote_info": vote_payload,
    }


def snapshot_goal_on_post(post: Post, goal: Goal) -> None:
    post.goal = goal
    post.goal_title = goal.title
    post.goal_start_date = _date_start_datetime(goal.start_date)
    post.goal_end_date = _date_end_datetime(goal.end_date)


def _date_start_datetime(d: Any) -> Any:

    dt = datetime.combine(d, time.min)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


def _date_end_datetime(d: Any) -> Any:

    dt = datetime.combine(d, time.max)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


def replace_post_tags(post: Post, tag_ids: list[int] | None) -> None:
    if not tag_ids:
        return
    tags = list(Tag.objects.filter(id__in=tag_ids, is_active=True))
    if len(tags) != len(set(tag_ids)):
        raise serializers.ValidationError({"tagIds": ["한 개 이상의 태그가 존재하지 않거나 비활성 태그입니다."]})
    PostTag.objects.filter(post=post).delete()
    PostTag.objects.bulk_create([PostTag(post=post, tag=t) for t in tags])


def active_comment_q() -> Any:

    return Q(comments__deleted_at__isnull=True) & ~Q(comments__status=CommentStatus.DELETED)
