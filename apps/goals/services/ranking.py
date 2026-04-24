from __future__ import annotations

import datetime

from django.utils import timezone

from apps.goals.models import Ranking
from apps.users.constants import PROFILE_IMAGE_URL_MAP


def get_weekly_ranking() -> list[dict[str, object]]:
    today = timezone.now().date()
    week_start = today - datetime.timedelta(days=today.weekday())

    rows = (
        Ranking.objects.filter(week_start=week_start, weekly_cert_count__gt=0)
        .select_related("user")
        .order_by("-weekly_cert_count", "calculated_at")
    )

    result = []
    for index, row in enumerate(rows, start=1):
        result.append(
            {
                "user_id": row.user.id,
                "nickname": row.user.nickname,
                "profile_img_url": PROFILE_IMAGE_URL_MAP.get(row.user.profile_image, ""),
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
        .order_by("-monthly_cert_count", "calculated_at")
    )

    result = []
    for index, row in enumerate(rows, start=1):
        result.append(
            {
                "user_id": row.user.id,
                "nickname": row.user.nickname,
                "profile_img_url": PROFILE_IMAGE_URL_MAP.get(row.user.profile_image, ""),
                "rank": index,
                "month_cert_count": row.monthly_cert_count,
            }
        )
    return result


def get_total_ranking() -> list[dict[str, object]]:
    rows = (
        Ranking.objects.filter(total_cert_count__gt=0)
        .select_related("user")
        .order_by("-total_cert_count", "calculated_at")
    )

    result = []
    for index, row in enumerate(rows, start=1):
        result.append(
            {
                "user_id": row.user.id,
                "nickname": row.user.nickname,
                "profile_img_url": PROFILE_IMAGE_URL_MAP.get(row.user.profile_image, ""),
                "rank": index,
                "total_cert_count": row.total_cert_count,
            }
        )
    return result
