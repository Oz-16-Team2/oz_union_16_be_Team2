import logging
from collections import defaultdict
from typing import Any

from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

from apps.posts.models import Post, PostLike, PostTag
from apps.users.models import User

logger = logging.getLogger(__name__)

_AUTHORED_WEIGHT: float = 5.0
_LIKED_WEIGHT: float = 3.0
_MAX_DAYS: float = 20.0
_CANDIDATE_LIMIT: int = 100


def _time_decay(age_days: float, max_days: float) -> float:
    """게시글 나이에 따른 감가율. 최소 0.1 보장 (완전히 묻히지 않도록)."""
    return max(0.1, 1.0 - age_days / max_days)


def get_recommended_posts(user: User, page: int = 1, size: int = 8) -> tuple[list[Post], int]:
    service = PostSuggestionService()
    posts = service.get_recommendations(user)
    total = len(posts)
    start = (page - 1) * size
    return posts[start : start + size], total


class PostSuggestionService:
    def get_recommendations(self, user: User, exclude_test_data: bool = False) -> list[Post]:
        queryset: QuerySet[Post] = Post.objects.all()

        if exclude_test_data or getattr(settings, "ENVIRONMENT", None) == "production":
            queryset = queryset.exclude(user__email__endswith="@test.com")

        return self._apply_recommendation_algorithm(user, queryset)

    def get_test_recommendations(self, user: User) -> list[Post]:
        test_posts: QuerySet[Post] = Post.objects.filter(user__email__endswith="@test.com")
        return self._apply_recommendation_algorithm(user, test_posts)

    def analyze_by_persona(self) -> dict[str, dict[int, dict[str, Any]]]:
        results: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)

        # 봇 유저 이메일 형식: {persona_prefix}_{i}@test.com
        persona_groups: dict[str, list[User]] = defaultdict(list)
        for user in User.objects.filter(email__endswith="@test.com"):
            local = user.email.split("@")[0]
            parts = local.rsplit("_", 1)
            persona = parts[0] if len(parts) == 2 and parts[1].isdigit() else local
            persona_groups[persona].append(user)

        for persona, users in persona_groups.items():
            for user in users:
                recommendations = self.get_recommendations(user)
                results[persona][user.pk] = self._calculate_metrics(user, recommendations)

        return results

    def _apply_recommendation_algorithm(self, user: User, queryset: QuerySet[Post]) -> list[Post]:
        tag_scores: dict[int, float] = defaultdict(float)

        for tag_id in PostTag.objects.filter(post__user=user).values_list("tag_id", flat=True):
            tag_scores[tag_id] += _AUTHORED_WEIGHT

        for tag_id in PostTag.objects.filter(post__likes__user=user).values_list("tag_id", flat=True):
            tag_scores[tag_id] += _LIKED_WEIGHT

        if not tag_scores:
            return list(queryset.exclude(user=user).order_by("-created_at")[:_CANDIDATE_LIMIT])

        now = timezone.now()
        interested_tag_ids = list(tag_scores.keys())

        # 태그가 겹치는 게시글만 먼저 필터링 후 최신순으로 후보 추출
        candidates = (
            queryset.exclude(user=user)
            .filter(post_tags__tag_id__in=interested_tag_ids)
            .distinct()
            .prefetch_related("post_tags")
            .order_by("-created_at")[: _CANDIDATE_LIMIT * 3]
        )

        scored: list[tuple[float, Post]] = []
        for post in candidates:
            post_tag_ids = [pt.tag_id for pt in post.post_tags.all()]
            score = sum((tag_scores.get(tid, 0.0) for tid in post_tag_ids), 0.0)
            if score == 0:
                continue

            age_days = (now - post.created_at).total_seconds() / 86400
            decay = _time_decay(age_days, _MAX_DAYS)
            scored.append((score * decay, post))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [post for _, post in scored[:_CANDIDATE_LIMIT]]

    def _calculate_metrics(self, user: User, recommendations: list[Post]) -> dict[str, Any]:
        if not recommendations:
            return {"precision": 0.0, "count": 0, "hits": 0}

        liked_ids = set(PostLike.objects.filter(user=user).values_list("post_id", flat=True))
        hits = sum(1 for post in recommendations if post.pk in liked_ids)
        return {
            "precision": round(hits / len(recommendations), 4),
            "count": len(recommendations),
            "hits": hits,
        }
