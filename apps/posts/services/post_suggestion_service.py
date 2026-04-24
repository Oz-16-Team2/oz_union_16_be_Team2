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

    def analyze_by_persona(
        self,
        persona_interested_tags: dict[str, list[str]] | None = None,
    ) -> dict[str, dict[int, dict[str, Any]]]:
        """
        페르소나별 추천 지표 분석.

        persona_interested_tags: persona 이름 → 관심 태그 목록 매핑.
          제공하면 tag_precision(추천 중 관심 태그 포함 비율)이 함께 집계된다.
        """
        results: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)

        # 봇 유저 이메일 형식: {persona_prefix}_{i}@test.com
        persona_groups: dict[str, list[User]] = defaultdict(list)
        for user in User.objects.filter(email__endswith="@test.com"):
            local = user.email.split("@")[0]
            parts = local.rsplit("_", 1)
            persona = parts[0] if len(parts) == 2 and parts[1].isdigit() else local
            persona_groups[persona].append(user)

        for persona, users in persona_groups.items():
            interested = (persona_interested_tags or {}).get(persona)
            for user in users:
                recommendations = self.get_recommendations(user)
                metrics = self._calculate_metrics(user, recommendations)
                metrics["tag_precision"] = self._tag_precision(recommendations, interested)
                results[persona][user.pk] = metrics

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
        """추천 중 관심 태그가 포함된 게시글 비율. interested_tags가 없거나 'all'이면 None."""
        if not recommendations or not interested_tags or "all" in interested_tags:
            return None
        tag_set = set(interested_tags)
        rec_ids = [post.pk for post in recommendations]
        matched_ids = set(
            PostTag.objects.filter(post_id__in=rec_ids, tag__name__in=tag_set).values_list("post_id", flat=True)
        )
        return round(len(matched_ids) / len(recommendations), 4)
