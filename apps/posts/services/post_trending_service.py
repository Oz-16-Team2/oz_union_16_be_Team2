from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Exists, OuterRef
from django.utils import timezone

from apps.posts.models import Scrap
from apps.posts.serializers.post_serializers import active_comment_q
from apps.posts.services.post_service import _base_visible_posts, get_tags_by_post_id
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User

_CONTENT_PREVIEW_LENGTH = 100

# period 선택지 → 며칠 이내
PERIOD_DAYS: dict[str, int] = {
    "day": 1,  # 지금 핫한 글 (24시간)
    "week": 7,  # 요즘 뜨는 글 (7일)
}
DEFAULT_PERIOD = "week"


def get_trending_posts(*, user: User, page: int, size: int, period: str) -> dict[str, Any]:
    days = PERIOD_DAYS.get(period, PERIOD_DAYS[DEFAULT_PERIOD])
    since = timezone.now() - timedelta(days=days)
    cq = active_comment_q()

    qs = (
        _base_visible_posts()
        .filter(is_private=False, created_at__gte=since)
        .select_related("user")
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", filter=cq, distinct=True),
            is_scrapped=Exists(Scrap.objects.filter(post_id=OuterRef("pk"), user_id=user.id)),
        )
        .order_by("-like_count", "-created_at")
    )

    total = qs.count()
    chunk = list(qs[(page - 1) * size : page * size])

    tag_map = get_tags_by_post_id([p.id for p in chunk])

    posts_out: list[dict[str, Any]] = []
    for p in chunk:
        preview = p.content[:_CONTENT_PREVIEW_LENGTH] if p.content else ""
        posts_out.append(
            {
                "post_id": p.id,
                "images": p.images or [],
                "profile_image_url": PROFILE_IMAGE_URL_MAP.get(p.user.profile_image),
                "nickname": p.user.nickname,
                "created_at": p.created_at,
                "title": p.title,
                "tags": tag_map.get(p.id, []),
                "content_preview": preview,
                "like_count": int(p.like_count),
                "comment_count": int(p.comment_count),
                "is_scrapped": bool(p.is_scrapped),
            }
        )

    return {"posts": posts_out, "page": page, "size": size, "total_count": total}
