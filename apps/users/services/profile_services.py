from __future__ import annotations

from typing import Any

from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User
from apps.users.services.common_services import _build_user_profile, _count_completed_goals, _get_goals_manager


def get_my_profile(user: User) -> dict[str, Any]:
    return _build_user_profile(user)


def get_me_activity_summary_days(user: Any) -> dict[str, Any]:
    created_at = getattr(user, "created_at", None)
    if created_at is None:
        days_together = 0
    else:
        from django.utils import timezone

        days_together = max((timezone.now().date() - created_at.date()).days, 0)

    return {"detail": {"days_together": days_together}}


def get_me_activity_summary_completed_goals(user: Any) -> dict[str, Any]:
    return {"detail": {"completed_goals_count": _count_completed_goals(user)}}


def get_me_activity_summary_achievement_rate(user: Any) -> dict[str, Any]:
    manager = _get_goals_manager(user)
    total_goals_count = int(manager.all().count()) if manager is not None else 0

    completed_goals_count = _count_completed_goals(user)
    total_achievement_rate = round((completed_goals_count / total_goals_count) * 100, 1) if total_goals_count else 0.0

    return {
        "detail": {
            "total_goals_count": total_goals_count,
            "completed_goals_count": completed_goals_count,
            "total_achievement_rate": total_achievement_rate,
        }
    }


class ProfileService:
    @staticmethod
    def get_profile_images() -> list[dict[str, str]]:
        return [{"code": str(code), "image_url": image_url} for code, image_url in PROFILE_IMAGE_URL_MAP.items()]
