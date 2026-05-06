from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Exists, OuterRef
from django.utils import timezone

from apps.posts.models import PostLike, Scrap
from apps.posts.serializers.post_serializers import active_comment_q
from apps.posts.services.post_service import _base_visible_posts, get_tags_by_post_id
from apps.posts.services.recommendation_config import (
    CONTENT_PREVIEW_LENGTH,
    TRENDING_DEFAULT_PERIOD,
    TRENDING_FALLBACK_THRESHOLD,
    TRENDING_HOT_SCORE_GRAVITY,
    TRENDING_PERIOD_DAYS,
    TRENDING_WEEK_CANDIDATE_LIMIT,
)
from apps.users.models import User
from apps.users.utils import get_user_display_info

PERIOD_DAYS = TRENDING_PERIOD_DAYS
DEFAULT_PERIOD = TRENDING_DEFAULT_PERIOD


def _hot_score(like_count: int, age_seconds: float) -> float:
    age_hours = max(0.0, age_seconds / 3600)  # 미래 날짜 게시글은 age=0으로 처리
    return float(like_count / (age_hours + 2) ** TRENDING_HOT_SCORE_GRAVITY)


def _build_posts_out(chunk: list[Any], tag_map: dict[int, list[str]]) -> list[dict[str, Any]]:
    posts_out: list[dict[str, Any]] = []
    for p in chunk:
        preview = p.content[:CONTENT_PREVIEW_LENGTH] if p.content else ""

        nickname, profile_url = get_user_display_info(p.user)

        posts_out.append(
            {
                "post_id": p.id,
                "images": p.images or [],
                "profile_image_url": profile_url,
                "nickname": nickname,
                "created_at": p.created_at,
                "title": p.title,
                "tags": tag_map.get(p.id, []),
                "content_preview": preview,
                "like_count": int(p.like_count),
                "comment_count": int(p.comment_count),
                "is_liked": bool(p.is_liked),
                "is_scrapped": bool(p.is_scrapped),
            }
        )
    return posts_out


def _get_base_qs(*, user: User, since: Any) -> Any:
    cq = active_comment_q()
    return (
        _base_visible_posts()
        .filter(is_private=False, created_at__gte=since)
        .select_related("user")
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", filter=cq, distinct=True),
            is_liked=Exists(PostLike.objects.filter(post_id=OuterRef("pk"), user_id=user.id)),
            is_scrapped=Exists(Scrap.objects.filter(post_id=OuterRef("pk"), user_id=user.id)),
        )
    )


def _trending_day(*, user: User, page: int, size: int, since: Any) -> dict[str, Any]:
    """24시간 이내 글을 누적 좋아요 수 내림차순으로 반환 (DB 정렬). page는 1-indexed."""
    qs = _get_base_qs(user=user, since=since).order_by("-like_count", "-created_at")
    total = qs.count()
    offset = (page - 1) * size
    chunk = list(qs[offset : offset + size])
    tag_map = get_tags_by_post_id([p.id for p in chunk])
    return {"posts": _build_posts_out(chunk, tag_map), "page": page, "size": size, "total_count": total}


def _trending_week(*, user: User, page: int, size: int, since: Any) -> dict[str, Any]:
    """7일 이내 글을 Hot Score 기준으로 반환.
    Hot Score = like_count / (age_hours + 2) ** gravity
    좋아요가 많아도 오래될수록 점수 감소 → 기간 초반 글의 순위 독점 완화.
    """
    now = timezone.now()
    # like_count 상위 후보를 먼저 DB에서 추려 메모리 부담 제한
    candidates = list(_get_base_qs(user=user, since=since).order_by("-like_count")[:TRENDING_WEEK_CANDIDATE_LIMIT])
    scored = sorted(
        candidates,
        key=lambda p: _hot_score(int(p.like_count), (now - p.created_at).total_seconds()),
        reverse=True,
    )
    total = len(scored)
    offset = (page - 1) * size
    chunk = scored[offset : offset + size]
    tag_map = get_tags_by_post_id([p.id for p in chunk])
    return {"posts": _build_posts_out(chunk, tag_map), "page": page, "size": size, "total_count": total}


def _get_latest_fallback(*, user: User, exclude_ids: list[int]) -> list[Any]:
    """trending 글이 부족할 때 최신순으로 보충할 후보를 반환."""
    active_comment_filter = active_comment_q()
    return list(
        _base_visible_posts()
        .filter(is_private=False)
        .exclude(id__in=exclude_ids)
        .select_related("user")
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", filter=active_comment_filter, distinct=True),
            is_liked=Exists(PostLike.objects.filter(post_id=OuterRef("pk"), user_id=user.id)),
            is_scrapped=Exists(Scrap.objects.filter(post_id=OuterRef("pk"), user_id=user.id)),
        )
        .order_by("-created_at")[:TRENDING_WEEK_CANDIDATE_LIMIT]
    )


def get_trending_posts(*, user: User, page: int, size: int, period: str) -> dict[str, Any]:
    days = PERIOD_DAYS.get(period, PERIOD_DAYS[DEFAULT_PERIOD])
    since = timezone.now() - timedelta(days=days)

    if period == "day":
        result = _trending_day(user=user, page=page, size=size, since=since)
    else:
        result = _trending_week(user=user, page=page, size=size, since=since)

    if result["total_count"] >= TRENDING_FALLBACK_THRESHOLD:
        return result

    # trending 글이 부족하면 최신순으로 보충하여 재페이지네이션
    if period == "day":
        all_trending = _trending_day(user=user, page=1, size=TRENDING_WEEK_CANDIDATE_LIMIT, since=since)
    else:
        all_trending = _trending_week(user=user, page=1, size=TRENDING_WEEK_CANDIDATE_LIMIT, since=since)

    all_trending_posts = all_trending["posts"]
    all_trending_ids = [post["post_id"] for post in all_trending_posts]

    fallback = _get_latest_fallback(user=user, exclude_ids=all_trending_ids)
    fallback_tag_map = get_tags_by_post_id([post.id for post in fallback])
    fallback_posts = _build_posts_out(fallback, fallback_tag_map)

    combined = all_trending_posts + fallback_posts
    total = len(combined)
    offset = (page - 1) * size
    chunk = combined[offset : offset + size]

    return {"posts": chunk, "page": page, "size": size, "total_count": total}
