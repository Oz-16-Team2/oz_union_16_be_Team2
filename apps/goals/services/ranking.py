from __future__ import annotations

import datetime
from typing import Any

from django.utils import timezone

from apps.goals.models import Ranking
from apps.users.constants import PROFILE_IMAGE_URL_MAP


def _get_user_display_info(user: Any) -> tuple[str, str]:
    social_info = user.social_logins.first()

    display_nickname = user.nickname
    if social_info and social_info.social_nickname:
        display_nickname = social_info.social_nickname

    display_profile_url = PROFILE_IMAGE_URL_MAP.get(user.profile_image, "")
    if social_info and social_info.social_profile_image_url:
        display_profile_url = social_info.social_profile_image_url
    elif user.social_profile_image_url:
        display_profile_url = user.social_profile_image_url

    return display_nickname, display_profile_url


def get_weekly_ranking() -> list[dict[str, object]]:
    today = timezone.now().date()
    week_start = today - datetime.timedelta(days=today.weekday())

    rows = (
        Ranking.objects.filter(week_start=week_start, weekly_cert_count__gt=0)
        .select_related("user")
        .prefetch_related("user__social_logins")
        .order_by("-weekly_cert_count", "calculated_at")
    )[:5]

    result = []
    for index, row in enumerate(rows, start=1):
        nickname, profile_url = _get_user_display_info(row.user)
        result.append(
            {
                "user_id": row.user.id,
                "nickname": nickname,
                "profile_img_url": profile_url,
                "rank": index,
                "week_cert_count": row.weekly_cert_count,
            }
        )
    return result


def get_monthly_ranking() -> list[dict[str, object]]:
    today = timezone.now().date()
    month_start = today.replace(day=1)

    rows = (
        Ranking.objects.filter(month_start=month_start, monthly_cert_count__gt=0)
        .select_related("user")
        .prefetch_related("user__social_logins")
        .order_by("-monthly_cert_count", "calculated_at")
    )[:5]

    result = []
    for index, row in enumerate(rows, start=1):
        nickname, profile_url = _get_user_display_info(row.user)
        result.append(
            {
                "user_id": row.user.id,
                "nickname": nickname,
                "profile_img_url": profile_url,
                "rank": index,
                "month_cert_count": row.monthly_cert_count,
            }
        )
    return result


def get_total_ranking() -> list[dict[str, object]]:
    rows = (
        Ranking.objects.filter(total_cert_count__gt=0)
        .select_related("user")
        .prefetch_related("user__social_logins")
        .order_by("-total_cert_count", "calculated_at")
    )[:5]

    result = []
    for index, row in enumerate(rows, start=1):
        nickname, profile_url = _get_user_display_info(row.user)
        result.append(
            {
                "user_id": row.user.id,
                "nickname": nickname,
                "profile_img_url": profile_url,
                "rank": index,
                "total_cert_count": row.total_cert_count,
            }
        )
    return result
