from __future__ import annotations

import datetime
from typing import Any

from django.db.models import Count

from apps.goals.models import CheckGoal


class AchievementService:
    @staticmethod
    def get_achievement(user: Any, start: datetime.date, end: datetime.date) -> list[dict[str, Any]]:
        rows = (
            CheckGoal.objects.filter(
                user=user,
                created_at__date__gte=start,
                created_at__date__lte=end,
            )
            .values("created_at__date")
            .annotate(check_count=Count("id"))
        )

        check_map: dict[datetime.date, int] = {row["created_at__date"]: row["check_count"] for row in rows}

        delta = end - start

        return [
            {
                "date": start + datetime.timedelta(days=i),
                "check_count": check_map.get(start + datetime.timedelta(days=i), 0),
            }
            for i in range(delta.days + 1)
        ]
