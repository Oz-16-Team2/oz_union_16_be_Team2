from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from django.utils import timezone
from rest_framework import serializers

from apps.core.choices import PostStatus, VoteStatus
from apps.goals.models import Goal
from apps.posts.models import Post, PostTag, Scrap
from apps.posts.serializers.post_serializers import (
    SCOPE_FEED,
    SCOPE_MY,
    SORT_LATEST,
    SORT_POPULAR,
    active_comment_q,
    build_feed_item,
    build_post_detail,
    replace_post_tags,
    snapshot_goal_on_post,
)
from apps.users.models import User
from apps.votes.models import Vote, VoteOption


def get_tags_by_post_id(post_ids: list[int]) -> dict[int, list[str]]:
    if not post_ids:
        return {}
    mapping: dict[int, list[str]] = {pid: [] for pid in post_ids}
    for pt in PostTag.objects.filter(post_id__in=post_ids).select_related("tag").order_by("post_id", "id").iterator():
        mapping.setdefault(pt.post_id, []).append(pt.tag.name)
    return mapping


def _base_visible_posts() -> Any:
    return Post.objects.filter(deleted_at__isnull=True, status=PostStatus.NORMAL)


def feed_queryset(*, scope: str, sort_by: str, user: User | AnonymousUser) -> Any:
    qs = _base_visible_posts().select_related("user", "goal")
    if scope == SCOPE_FEED:
        qs = qs.filter(is_private=False)
    elif scope == SCOPE_MY:
        if not user.is_authenticated:
            raise serializers.ValidationError({"scope": ["MY scope requires authentication."]})
        qs = qs.filter(user=user)
    cq = active_comment_q()
    qs = qs.annotate(
        like_count=Count("likes", distinct=True),
        comment_count=Count("comments", filter=cq, distinct=True),
    )
    if user.is_authenticated:
        qs = qs.annotate(
            is_scrapped=Exists(Scrap.objects.filter(post_id=OuterRef("pk"), user_id=user.id)),
        )
    else:
        qs = qs.annotate(is_scrapped=Value(False, output_field=BooleanField()))
    if sort_by == SORT_LATEST:
        qs = qs.order_by("-created_at")
    elif sort_by == SORT_POPULAR:
        qs = qs.order_by("-like_count", "-created_at")
    return qs


def list_posts(*, scope: str, sort_by: str, page: int, size: int, user: User | AnonymousUser) -> dict[str, Any]:
    qs = feed_queryset(scope=scope, sort_by=sort_by, user=user)
    total = qs.count()
    chunk = qs[page * size : page * size + size]
    ids = [p.id for p in chunk]
    tags_map = get_tags_by_post_id(ids)
    posts_out = [
        build_feed_item(
            p,
            tags=tags_map.get(p.id, []),
            like_count=p.like_count,
            comment_count=p.comment_count,
            is_scrapped=bool(p.is_scrapped),
        )
        for p in chunk
    ]
    return {"posts": posts_out, "page": page, "size": size, "total_count": total}


def _get_post_for_detail(post_id: int) -> Post:
    post = (
        Post.objects.filter(id=post_id, deleted_at__isnull=True)
        .select_related("user", "goal")
        .prefetch_related("post_tags__tag")
        .first()
    )
    if post is None:
        raise serializers.ValidationError({"postId": ["해당 게시글(객체)을 찾을 수 없습니다."]})
    return post


def can_view_post(post: Post, user: User | AnonymousUser) -> bool:
    if not post.is_private:
        return True
    return bool(user.is_authenticated and post.user_id == user.id)


def get_post_detail(*, post_id: int, user: User | AnonymousUser) -> dict[str, Any]:
    post = _get_post_for_detail(post_id)
    if not can_view_post(post, user):
        raise serializers.ValidationError({"postId": ["해당 게시글(객체)을 찾을 수 없습니다."]})
    cq = active_comment_q()
    agg = Post.objects.filter(pk=post.pk).aggregate(
        like_count=Count("likes", distinct=True),
        comment_count=Count("comments", filter=cq, distinct=True),
    )
    is_scrapped = False
    if user.is_authenticated:
        is_scrapped = Scrap.objects.filter(post_id=post.id, user_id=user.id).exists()
    tags = [pt.tag.name for pt in post.post_tags.all()]
    vote_payload = None
    vote_obj = Vote.objects.filter(post=post).prefetch_related("options").first()
    if vote_obj is not None:
        opts = sorted(vote_obj.options.all(), key=lambda o: o.sort_order)
        vote_payload = {
            "vote_id": vote_obj.id,
            "question": vote_obj.question,
            "end_at": vote_obj.end_at,
            "status": vote_obj.status,
            "options": [{"option_id": o.id, "content": o.content, "sort_order": o.sort_order} for o in opts],
        }
    return build_post_detail(
        post,
        tags=tags,
        like_count=int(agg["like_count"] or 0),
        comment_count=int(agg["comment_count"] or 0),
        is_scrapped=is_scrapped,
        vote_payload=vote_payload,
    )


def _create_vote_for_post(post: Post, vote_data: dict[str, Any]) -> None:
    now = timezone.now()
    vote = Vote.objects.create(
        post=post,
        question=vote_data["question"],
        start_at=now,
        end_at=now + timedelta(days=7),
        status=VoteStatus.IN_PROGRESS,
    )
    for opt in vote_data["options"]:
        VoteOption.objects.create(
            vote=vote,
            content=opt["content"],
            sort_order=opt["sort_order"],
        )


def _clear_goal_fields(post: Post) -> None:
    post.goal = None
    post.goal_title = None
    post.goal_start_date = None
    post.goal_end_date = None
    post.goal_progress = None


@transaction.atomic
def create_post(user: User, data: dict[str, Any]) -> Post:
    post = Post(
        user=user,
        title=data["title"],
        content=data["content"],
        images=data.get("images") or [],
        is_private=data.get("is_private", False),
    )
    if data.get("has_goal") and data.get("goal_id"):
        goal = Goal.objects.filter(pk=data["goal_id"], user=user).first()
        if goal is None:
            raise serializers.ValidationError({"goalId": ["Goal not found."]})
        snapshot_goal_on_post(post, goal)
    post.save()
    replace_post_tags(post, data.get("tag_ids") or [])
    if data.get("has_vote") and data.get("vote"):
        _create_vote_for_post(post, data["vote"])
    return post


def _ensure_owner(post: Post, user: User, *, action: str = "modify") -> None:
    if not user.is_authenticated or post.user_id != user.id:
        raise serializers.ValidationError(
            {"Authorization": [f"You do not have permission to {action} this post."]},
        )


@transaction.atomic
def update_post(*, user: User, url_post_id: int, data: dict[str, Any]) -> None:

    post = Post.objects.filter(id=url_post_id, deleted_at__isnull=True).first()
    if post is None:
        raise serializers.ValidationError({"postId": ["Post not found."]})
    _ensure_owner(post, user, action="modify")
    if "title" in data:
        post.title = data["title"]
    if "content" in data:
        post.content = data["content"]
    if "images" in data:
        post.images = data["images"]
    if "is_private" in data:
        post.is_private = data["is_private"]
    if data.get("has_goal") is False:
        _clear_goal_fields(post)
    elif data.get("goal_id"):
        goal = Goal.objects.filter(pk=data["goal_id"], user=user).first()
        if goal is None:
            raise serializers.ValidationError({"goalId": ["Goal not found."]})
        snapshot_goal_on_post(post, goal)

    if data.get("has_vote") is False:
        Vote.objects.filter(post=post).delete()
    if "tag_ids" in data:
        replace_post_tags(post, data["tag_ids"])
    post.save()


@transaction.atomic
def soft_delete_post(*, user: User, post_id: int) -> None:
    post = Post.objects.filter(id=post_id, deleted_at__isnull=True).first()
    if post is None:
        raise serializers.ValidationError({"postId": ["Post not found."]})
    _ensure_owner(post, user, action="delete")
    post.deleted_at = timezone.now()
    post.save()
