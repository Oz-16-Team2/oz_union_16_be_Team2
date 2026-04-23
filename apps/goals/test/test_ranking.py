from __future__ import annotations

import datetime

import pytest
from django.urls import reverse
from django.utils.timezone import make_aware
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from apps.goals.models import Ranking
from apps.users.models import User


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db: object) -> User:
    return User.objects.create_user(
        email="test@example.com",
        password="password123",
        nickname="tester1",
    )


@pytest.fixture
def another_user(db: object) -> User:
    return User.objects.create_user(
        email="test2@example.com",
        password="password123",
        nickname="tester2",
    )


@pytest.fixture
def weekly_ranking(db: object, user: User, another_user: User) -> None:
    Ranking.objects.create(
        user=user,
        weekly_rank=2,
        weekly_cert_count=10,
        week_start=datetime.date(2026, 4, 13),
        calculated_at=make_aware(datetime.datetime(2026, 4, 13)),
    )
    Ranking.objects.create(
        user=another_user,
        weekly_rank=1,
        weekly_cert_count=20,
        week_start=datetime.date(2026, 4, 13),
        calculated_at=make_aware(datetime.datetime(2026, 4, 13)),
    )


@pytest.fixture
def monthly_ranking(db: object, user: User, another_user: User) -> None:
    Ranking.objects.create(
        user=user,
        monthly_rank=2,
        monthly_cert_count=30,
        month_start=datetime.date(2026, 4, 1),
        calculated_at=make_aware(datetime.datetime(2026, 4, 15)),
    )
    Ranking.objects.create(
        user=another_user,
        monthly_rank=1,
        monthly_cert_count=50,
        month_start=datetime.date(2026, 4, 1),
        calculated_at=make_aware(datetime.datetime(2026, 4, 15)),
    )


@pytest.fixture
def total_ranking(db: object, user: User, another_user: User) -> None:
    Ranking.objects.create(
        user=user, total_rank=2, total_cert_count=100, calculated_at=make_aware(datetime.datetime(2026, 4, 13))
    )
    Ranking.objects.create(
        user=another_user, total_rank=1, total_cert_count=200, calculated_at=make_aware(datetime.datetime(2026, 4, 13))
    )


@pytest.mark.django_db
class TestWeeklyRanking:
    @freeze_time("2026-04-15")
    def test_success(self, client: APIClient, weekly_ranking: None) -> None:
        response = client.get(reverse("weekly-ranking"))

        assert response.status_code == status.HTTP_200_OK
        rankings = response.data["detail"]["rankings"]
        assert len(rankings) == 2
        assert rankings[0]["rank"] == 1
        assert rankings[0]["week_cert_count"] == 20

    @freeze_time("2026-04-15")
    def test_no_data_for_current_week(self, client: APIClient) -> None:
        response = client.get(reverse("weekly-ranking"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"]["rankings"] == []

    @freeze_time("2026-04-15")
    def test_ordered_by_rank(self, client: APIClient, weekly_ranking: None, another_user: User) -> None:
        response = client.get(reverse("weekly-ranking"))

        rankings = response.data["detail"]["rankings"]
        assert rankings[0]["user_id"] == another_user.id
        assert rankings[0]["rank"] == 1


@pytest.mark.django_db
class TestMonthlyRanking:
    @freeze_time("2026-04-15")
    def test_success(self, client: APIClient, monthly_ranking: None) -> None:
        response = client.get(reverse("monthly-ranking"))

        assert response.status_code == status.HTTP_200_OK
        rankings = response.data["detail"]["rankings"]
        assert len(rankings) == 2
        assert rankings[0]["rank"] == 1
        assert rankings[0]["month_cert_count"] == 50

    @freeze_time("2026-04-15")
    def test_no_data_for_current_month(self, client: APIClient) -> None:
        response = client.get(reverse("monthly-ranking"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"]["rankings"] == []

    @freeze_time("2026-04-15")
    def test_ordered_by_rank(self, client: APIClient, monthly_ranking: None, another_user: User) -> None:
        response = client.get(reverse("monthly-ranking"))

        rankings = response.data["detail"]["rankings"]
        assert rankings[0]["rank"] == 1


@pytest.mark.django_db
class TestTotalRanking:
    def test_success(self, client: APIClient, total_ranking: None) -> None:
        response = client.get(reverse("total-ranking"))

        assert response.status_code == status.HTTP_200_OK
        rankings = response.data["detail"]["rankings"]
        assert len(rankings) == 2
        assert rankings[0]["rank"] == 1
        assert rankings[0]["total_cert_count"] == 200

    def test_empty(self, client: APIClient) -> None:
        response = client.get(reverse("total-ranking"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"]["rankings"] == []

    def test_ordered_by_rank(self, client: APIClient, total_ranking: None, another_user: User) -> None:
        response = client.get(reverse("total-ranking"))

        rankings = response.data["detail"]["rankings"]
        assert rankings[0]["user_id"] == another_user.id
        assert rankings[0]["total_cert_count"] == 200
