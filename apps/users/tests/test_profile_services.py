from datetime import timedelta
from typing import Any
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone

from apps.users.services.profile_services import (
    get_me_activity_summary_achievement_rate,
    get_me_activity_summary_completed_goals,
    get_me_activity_summary_days,
    get_my_profile,
)


@pytest.mark.django_db
def test_get_my_profile(user: Any) -> None:
    result = get_my_profile(user)

    assert result["id"] == user.id
    assert result["nickname"] == user.nickname
    assert "profile_image_url" in result


def test_get_me_activity_summary_days_with_created_at() -> None:
    user = Mock()
    user.created_at = timezone.now() - timedelta(days=3)

    result = get_me_activity_summary_days(user)

    assert result == {"detail": {"days_together": 3}}


def test_get_me_activity_summary_days_without_created_at() -> None:
    user = Mock()
    user.created_at = None

    result = get_me_activity_summary_days(user)

    assert result == {"detail": {"days_together": 0}}


def test_get_me_activity_summary_completed_goals() -> None:
    user = Mock()

    with patch("apps.users.services.profile_services._count_completed_goals", return_value=5):
        result = get_me_activity_summary_completed_goals(user)

    assert result == {"detail": {"completed_goals_count": 5}}


def test_get_me_activity_summary_achievement_rate() -> None:
    user = Mock()
    manager = Mock()
    manager.all.return_value.count.return_value = 10

    with (
        patch("apps.users.services.profile_services._get_goals_manager", return_value=manager),
        patch("apps.users.services.profile_services._count_completed_goals", return_value=7),
    ):
        result = get_me_activity_summary_achievement_rate(user)

    assert result == {
        "detail": {
            "total_goals_count": 10,
            "completed_goals_count": 7,
            "total_achievement_rate": 70.0,
        }
    }


def test_get_me_activity_summary_achievement_rate_without_goals() -> None:
    user = Mock()

    with (
        patch("apps.users.services.profile_services._get_goals_manager", return_value=None),
        patch("apps.users.services.profile_services._count_completed_goals", return_value=0),
    ):
        result = get_me_activity_summary_achievement_rate(user)

    assert result["detail"]["total_goals_count"] == 0
    assert result["detail"]["total_achievement_rate"] == 0.0
