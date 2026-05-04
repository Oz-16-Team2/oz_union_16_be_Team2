import logging
from collections import defaultdict
from typing import Any

from django.conf import settings
from django.db.models import Count, QuerySet
from django.utils import timezone

from apps.posts.models import Post, PostLike, PostTag, Scrap
from apps.posts.serializers.post_serializers import active_comment_q
from apps.posts.services.recommendation_config import (
    CONTENT_PREVIEW_LENGTH,
    SUGGESTION_AUTHORED_WEIGHT,
    SUGGESTION_CANDIDATE_LIMIT,
    SUGGESTION_LIKED_WEIGHT,
    SUGGESTION_TIME_DECAY_MAX_DAYS,
)
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User

logger = logging.getLogger(__name__)


def _time_decay(age_days: float) -> float:
    """게시글 나이에 따른 감가율. 최소 0.1 보장."""
    return max(0.1, 1.0 - age_days / SUGGESTION_TIME_DECAY_MAX_DAYS)


def get_recommended_posts(user: User, page: int = 1, size: int = 8) -> tuple[list[Post], int]:
    service = PostSuggestionService()
    posts = service.get_recommendations(user)
    total = len(posts)
    start = (page - 1) * size
    return posts[start : start + size], total


def _enrich_posts(posts: list[Post], *, user: User) -> list[dict[str, Any]]:
    if not posts:
        return []

    post_ids = [p.pk for p in posts]
    cq = active_comment_q()

    counts: dict[int, dict[str, int]] = {
        int(row["id"]): {"like_count": int(row["like_count"]), "comment_count": int(row["comment_count"])}
        for row in Post.objects.filter(id__in=post_ids)
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", filter=cq, distinct=True),
        )
        .values("id", "like_count", "comment_count")
    }

    tag_map: dict[int, list[str]] = {pid: [] for pid in post_ids}
    for pt in PostTag.objects.filter(post_id__in=post_ids).select_related("tag").order_by("post_id", "id"):
        tag_map[pt.post_id].append(pt.tag.name)

    scrapped_ids = set(Scrap.objects.filter(post_id__in=post_ids, user=user).values_list("post_id", flat=True))
    liked_ids = set(PostLike.objects.filter(post_id__in=post_ids, user=user).values_list("post_id", flat=True))

    items: list[dict[str, Any]] = []
    for p in posts:
        c = counts.get(p.pk, {})
        preview = p.content[:CONTENT_PREVIEW_LENGTH] if p.content else ""
        items.append(
            {
                "post_id": p.pk,
                "images": p.images or [],
                "profile_image_url": p.user.social_profile_image_url
                or PROFILE_IMAGE_URL_MAP.get(p.user.profile_image, ""),
                "nickname": p.user.nickname,
                "created_at": p.created_at,
                "title": p.title,
                "tags": tag_map.get(p.pk, []),
                "content_preview": preview,
                "like_count": c.get("like_count", 0),
                "comment_count": c.get("comment_count", 0),
                "is_liked": p.pk in liked_ids,
                "is_scrapped": p.pk in scrapped_ids,
            }
        )
    return items


def get_recommendation_feed(*, user: User, page: int = 0, size: int = 8) -> dict[str, Any]:
    chunk, total = get_recommended_posts(user=user, page=page + 1, size=size)
    return {
        "posts": _enrich_posts(chunk, user=user),
        "page": page,
        "size": size,
        "total_count": total,
    }


class PostSuggestionService:
    def get_recommendations(self, user: User) -> list[Post]:
        queryset: QuerySet[Post] = Post.objects.all()

        if getattr(settings, "ENVIRONMENT", None) == "production":
            queryset = queryset.exclude(user__email__endswith="@test.com")

        return self._apply_recommendation_algorithm(user, queryset)

    def _apply_recommendation_algorithm(self, user: User, queryset: QuerySet[Post]) -> list[Post]:
        tag_scores: dict[int, float] = defaultdict(float)

        for tag_id in PostTag.objects.filter(post__user=user).values_list("tag_id", flat=True):
            tag_scores[tag_id] += SUGGESTION_AUTHORED_WEIGHT

        for tag_id in PostTag.objects.filter(post__likes__user=user).values_list("tag_id", flat=True):
            tag_scores[tag_id] += SUGGESTION_LIKED_WEIGHT

        if not tag_scores:
            return list(
                queryset.exclude(user=user).select_related("user").order_by("-created_at")[:SUGGESTION_CANDIDATE_LIMIT]
            )

        now = timezone.now()
        interested_tag_ids = list(tag_scores.keys())

        candidates = (
            queryset.exclude(user=user)
            .filter(post_tags__tag_id__in=interested_tag_ids)
            .distinct()
            .select_related("user")
            .prefetch_related("post_tags")
            .order_by("-created_at")[: SUGGESTION_CANDIDATE_LIMIT * 3]
        )

        scored: list[tuple[float, Post]] = []
        for post in candidates:
            post_tag_ids = [pt.tag_id for pt in post.post_tags.all()]
            score = sum((tag_scores.get(tid, 0.0) for tid in post_tag_ids), 0.0)
            if score == 0:
                continue

            age_days = (now - post.created_at).total_seconds() / 86400
            decay = _time_decay(age_days)
            scored.append((score * decay, post))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [post for _, post in scored[:SUGGESTION_CANDIDATE_LIMIT]]

    def _calculate_metrics(self, user: User, recommendations: list[Post]) -> dict[str, Any]:
        if not recommendations:
            return {"precision": 0.0, "count": 0, "hits": 0, "random_baseline": 0.0, "lift": 0.0}

        liked_ids = set(PostLike.objects.filter(user=user).values_list("post_id", flat=True))
        hits = sum(1 for post in recommendations if post.pk in liked_ids)
        precision = round(hits / len(recommendations), 4)

        total_candidates = Post.objects.exclude(user=user).count()
        random_baseline = round(len(liked_ids) / total_candidates, 4) if total_candidates > 0 else 0.0
        lift = round(precision / random_baseline, 2) if random_baseline > 0 else 0.0

        return {
            "precision": precision,
            "count": len(recommendations),
            "hits": hits,
            "random_baseline": random_baseline,
            "lift": lift,
        }

    def _tag_precision(self, recommendations: list[Post], interested_tags: list[str] | None) -> float | None:
        if not recommendations or not interested_tags or "all" in interested_tags:
            return None
        tag_set = set(interested_tags)
        rec_ids = [post.pk for post in recommendations]
        matched_ids = set(
            PostTag.objects.filter(post_id__in=rec_ids, tag__name__in=tag_set).values_list("post_id", flat=True)
        )
        return round(len(matched_ids) / len(recommendations), 4)
