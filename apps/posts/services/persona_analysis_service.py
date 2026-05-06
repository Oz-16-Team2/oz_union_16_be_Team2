"""
페르소나 시뮬레이션 분석 서비스.
management command(check_suggestions) 전용 — 프로덕션 API에서는 호출하지 않습니다.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from apps.posts.models import Post, PostTag
from apps.posts.services.post_suggestion_service import PostSuggestionService
from apps.users.models import User


def analyze_by_persona(
    persona_interested_tags: dict[str, list[str]] | None = None,
) -> dict[str, dict[int, dict[str, Any]]]:
    """
    페르소나별 추천 품질 분석.
    persona_interested_tags: persona 이름 → 관심 태그 목록 매핑.
    """
    service = PostSuggestionService()
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
            recommendations = service.get_recommendations(user)
            metrics = service._calculate_metrics(user, recommendations)
            metrics["tag_precision"] = _tag_precision(recommendations, interested)
            results[persona][user.pk] = metrics

    return results


def get_test_recommendations(user: User) -> list[Post]:
    """봇 데이터(@test.com)만 대상으로 추천 결과 반환. 시뮬레이션 전용."""
    test_posts = Post.objects.filter(user__email__endswith="@test.com")
    return PostSuggestionService()._apply_recommendation_algorithm(user, test_posts)


def _tag_precision(recommendations: list[Post], interested_tags: list[str] | None) -> float | None:
    if not recommendations or not interested_tags or "all" in interested_tags:
        return None
    tag_set = set(interested_tags)
    rec_ids = [post.pk for post in recommendations]
    matched_ids = set(
        PostTag.objects.filter(post_id__in=rec_ids, tag__name__in=tag_set).values_list("post_id", flat=True)
    )
    return round(len(matched_ids) / len(recommendations), 4)
