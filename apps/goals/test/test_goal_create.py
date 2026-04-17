from collections.abc import Generator
from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.goals.models import Goal
from apps.users.models import User


@pytest.mark.django_db
class TestGoalAPI:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class_data(self, django_db_blocker: Any) -> Generator[dict[str, Any]]:
        with django_db_blocker.unblock():
            user = User.objects.create_user(nickname="me", email="me@test.com", password="pass")
            other = User.objects.create_user(nickname="other", email="other@test.com", password="pass")

            goal = Goal.objects.create(user=user, title="내 목표", start_date="2026-04-14", end_date="2026-05-14")
            other_goal = Goal.objects.create(
                user=other, title="남의 목표", start_date="2026-04-14", end_date="2026-05-14"
            )

            yield {
                "user": user,
                "goal": goal,
                "other_goal": other_goal,
                "list_url": reverse("goal-create"),
                "detail_url": reverse("goal-detail", kwargs={"goal_id": goal.id}),
                "other_detail_url": reverse("goal-detail", kwargs={"goal_id": other_goal.id}),
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

    def test_update_goal_success(self) -> None:
        data = {"title": "수정된 제목"}
        response = self.client.patch(self.data["detail_url"], data)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_goal_success(self) -> None:
        response = self.client.delete(self.data["detail_url"])
        assert response.status_code == status.HTTP_200_OK
        assert not Goal.objects.filter(id=self.data["goal"].id).exists()
