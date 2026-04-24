from __future__ import annotations

import datetime

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from apps.goals.models import CheckGoal, Goal
from apps.users.models import User


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db: object) -> User:
    return User.objects.create_user(
        email="test@example.com",
        password="password123",
        nickname="tester",
    )


@pytest.fixture
def goal(db: object, user: User) -> Goal:
    return Goal.objects.create(
        user=user,
        title="test goal",
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 12, 31),
    )


@pytest.mark.django_db
class TestAchievement:
    def test_success(self, client: APIClient, user: User, goal: Goal) -> None:
        with freeze_time("2026-04-23"):
            CheckGoal.objects.create(user=user, goal=goal)
            CheckGoal.objects.create(user=user, goal=goal)

        client.force_authenticate(user=user)
        response = client.get(reverse("heatmap"), {"start": "2026-01-01", "end": "2026-12-31"})

        assert response.status_code == status.HTTP_200_OK
        days = response.data["detail"]["days"]
        assert len(days) == 365

        april_23 = next(d for d in days if str(d["date"]) == "2026-04-23")
        assert april_23["check_count"] == 2

    def test_no_check_returns_zero(self, client: APIClient, user: User) -> None:
        client.force_authenticate(user=user)
        response = client.get(reverse("heatmap"), {"start": "2026-01-01", "end": "2026-12-31"})

        assert response.status_code == status.HTTP_200_OK
        days = response.data["detail"]["days"]
        assert all(d["check_count"] == 0 for d in days)

    def test_missing_params(self, client: APIClient, user: User) -> None:
        client.force_authenticate(user=user)
        response = client.get(reverse("heatmap"))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error_detail" in response.data

    def test_start_after_end(self, client: APIClient, user: User) -> None:
        client.force_authenticate(user=user)
        response = client.get(reverse("heatmap"), {"start": "2026-12-31", "end": "2026-01-01"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated(self, client: APIClient) -> None:
        response = client.get(reverse("heatmap"), {"start": "2026-01-01", "end": "2026-12-31"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_only_own_data(self, client: APIClient, user: User, goal: Goal) -> None:
        other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            nickname="other",
        )
        other_goal = Goal.objects.create(
            user=other_user,
            title="other goal",
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 12, 31),
        )
        with freeze_time("2026-04-23"):
            CheckGoal.objects.create(user=other_user, goal=other_goal)

        client.force_authenticate(user=user)
        response = client.get(reverse("heatmap"), {"start": "2026-01-01", "end": "2026-12-31"})

        days = response.data["detail"]["days"]
        assert all(d["check_count"] == 0 for d in days)

    def test_partial_range(self, client: APIClient, user: User, goal: Goal) -> None:
        with freeze_time("2026-04-23"):
            CheckGoal.objects.create(user=user, goal=goal)

        client.force_authenticate(user=user)
        response = client.get(reverse("heatmap"), {"start": "2026-04-01", "end": "2026-04-30"})

        assert response.status_code == status.HTTP_200_OK
        days = response.data["detail"]["days"]
        assert len(days) == 30

        april_23 = next(d for d in days if str(d["date"]) == "2026-04-23")
        assert april_23["check_count"] == 1

    def test_leap_year(self, client: APIClient, user: User) -> None:
        client.force_authenticate(user=user)
        response = client.get(reverse("heatmap"), {"start": "2024-01-01", "end": "2024-12-31"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["detail"]["days"]) == 366
