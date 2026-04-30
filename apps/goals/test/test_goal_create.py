from collections.abc import Generator
from datetime import timedelta
from typing import Any

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.choices import Status
from apps.goals.models import CheckGoal, Goal
from apps.users.models import User


@pytest.mark.django_db
class TestGoalAPI:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class_data(self, django_db_blocker: Any) -> Generator[dict[str, Any]]:
        with django_db_blocker.unblock():
            user = User.objects.create_user(nickname="me", email="me@test.com", password="pass")
            other = User.objects.create_user(nickname="other", email="other@test.com", password="pass")
            today = timezone.now().date()

            goal = Goal.objects.create(user=user, title="내 목표", start_date="2026-04-14", end_date="2026-05-14")
            other_goal = Goal.objects.create(
                user=other, title="남의 목표", start_date="2026-04-14", end_date="2026-05-14"
            )

            expired_goal = Goal.objects.create(
                user=user,
                title="만료됨",
                start_date=today - timedelta(days=10),
                end_date=today - timedelta(days=1),
                status=Status.IN_PROGRESS,
            )

            completed_goal = Goal.objects.create(
                user=user,
                title="완료됨",
                start_date=today - timedelta(days=5),
                end_date=today + timedelta(days=5),
                status=Status.COMPLETED,
            )

            yield {
                "user": user,
                "goal": goal,
                "other_goal": other_goal,
                "expired_goal": expired_goal,
                "completed_goal": completed_goal,
                "list_url": reverse("goal-create"),
                "detail_url": reverse("goal-detail", kwargs={"goal_id": goal.id}),
                "other_detail_url": reverse("goal-detail", kwargs={"goal_id": other_goal.id}),
                "completed_detail_url": reverse("goal-detail", kwargs={"goal_id": completed_goal.id}),
            }

    @pytest.fixture(autouse=True)
    def setup_method(self, setup_class_data: dict[str, Any]) -> None:
        self.data = setup_class_data
        self.client = APIClient()
        self.client.force_authenticate(user=self.data["user"])

    def test_get_goal_list(self) -> None:
        response = self.client.get(self.data["list_url"])
        assert response.status_code == status.HTTP_200_OK

    def test_get_goal_detail_success(self) -> None:
        response = self.client.get(self.data["detail_url"])
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "내 목표"

    def test_get_other_goal_detail_fail(self) -> None:
        response = self.client.get(self.data["other_detail_url"])
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_goal_success(self) -> None:
        data = {"title": "신규", "start_date": "2026-04-15", "end_date": "2026-05-15"}
        response = self.client.post(self.data["list_url"], data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_goal_invalid_date(self) -> None:
        data = {"title": "잘못된 날짜", "start_date": "2026-05-15", "end_date": "2026-04-14"}
        response = self.client.post(self.data["list_url"], data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_goal_success(self) -> None:
        data = {"title": "수정된 제목"}
        response = self.client.patch(self.data["detail_url"], data)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_goal_success(self) -> None:
        response = self.client.delete(self.data["detail_url"])
        assert response.status_code == status.HTTP_200_OK
        assert not Goal.objects.filter(id=self.data["goal"].id).exists()

    def test_get_goal_list_status_filter(self) -> None:
        response = self.client.get(self.data["list_url"], {"status": "in_progress"})
        assert response.status_code == status.HTTP_200_OK

    def test_get_goal_list_date_filter(self) -> None:
        response = self.client.get(self.data["list_url"], {"start": "2026-04-01", "end": "2026-05-31"})
        assert response.status_code == status.HTTP_200_OK

    def test_get_goal_list_pagination(self) -> None:
        response = self.client.get(self.data["list_url"], {"page": 1, "size": 5})
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_get_goal_list_updates_expired_status(self) -> None:
        response = self.client.get(self.data["list_url"])
        assert response.status_code == status.HTTP_200_OK

        expired_goal = Goal.objects.get(id=self.data["expired_goal"].id)
        assert expired_goal.status != Status.IN_PROGRESS

    def test_update_completed_goal_fails(self) -> None:
        data = {"title": "수정 시도"}
        response = self.client.patch(self.data["completed_detail_url"], data)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "진행 중인 목표만 수정할 수 있습니다" in str(response.data["error_detail"])

    def test_update_goal_status_defensive_return(self) -> None:
        from apps.goals.services.goal_create import GoalCreateService

        active_goal = Goal.objects.get(id=self.data["goal"].id)

        GoalCreateService.update_goal_status(active_goal)

        assert active_goal.status == Status.IN_PROGRESS

    def test_update_goal_status_completed_branch(self) -> None:
        from datetime import timedelta

        from django.utils import timezone

        from apps.goals.services.goal_create import GoalCreateService

        today = timezone.now().date()
        user = self.data["user"]

        perfect_goal = Goal.objects.create(
            user=user,
            title="완벽히 달성하고 만료됨",
            start_date=today - timedelta(days=2),
            end_date=today - timedelta(days=1),
            status=Status.IN_PROGRESS,
        )

        CheckGoal.objects.create(user=user, goal=perfect_goal)
        CheckGoal.objects.create(user=user, goal=perfect_goal)

        GoalCreateService.update_goal_status(perfect_goal)

        assert perfect_goal.status == Status.COMPLETED


@pytest.mark.django_db
class TestGoalCheckedHistoryAPI:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class_data(self, django_db_blocker: Any) -> Generator[dict[str, Any]]:
        with django_db_blocker.unblock():
            user = User.objects.create_user(nickname="historyuser", email="history@test.com", password="pass")
            goal = Goal.objects.create(user=user, title="잔디 목표", start_date="2026-04-01", end_date="2026-04-30")
            CheckGoal.objects.create(user=user, goal=goal)

            yield {
                "user": user,
                "goal": goal,
                "url": reverse("goal-history"),
            }

    @pytest.fixture(autouse=True)
    def setup_method(self, setup_class_data: dict[str, Any]) -> None:
        self.data = setup_class_data
        self.client = APIClient()
        self.client.force_authenticate(user=self.data["user"])

    def test_get_checked_history_success(self) -> None:
        from django.utils import timezone

        today = timezone.now().date().isoformat()
        response = self.client.get(self.data["url"], {"date": today})
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_get_checked_history_missing_date(self) -> None:
        response = self.client.get(self.data["url"])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error_detail" in response.data

    def test_get_checked_history_no_result(self) -> None:
        response = self.client.get(self.data["url"], {"date": "2000-01-01"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
