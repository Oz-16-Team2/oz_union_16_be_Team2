import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.choices import Status
from apps.goals.models import Goal
from apps.users.models import User


@pytest.mark.django_db
class TestGoalCheckAPI:
    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        self.user = User.objects.create_user(
            nickname="checkuser",
            email="check@test.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            nickname="otheruser",
            email="otheru@test.com",
            password="password123",
        )
        self.goal = Goal.objects.create(
            user=self.user,
            title="인증용 목표",
            start_date="2026-04-14",
            end_date="2026-05-14",
            status=Status.IN_PROGRESS,
        )
        self.check_url = reverse("goal-check", kwargs={"goal_id": self.goal.id})

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_check_goal_success(self) -> None:
        response = self.client.post(self.check_url)
        assert response.status_code == status.HTTP_200_OK

    def test_check_goal_already_checked_fail(self) -> None:
        self.client.post(self.check_url)
        response = self.client.post(self.check_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_check_other_user_goal_fail(self) -> None:
        other_goal = Goal.objects.create(
            user=self.other_user,
            title="남의 것",
            start_date="2026-04-14",
            end_date="2026-05-14",
            status=Status.IN_PROGRESS,
        )
        url = reverse("goal-check", kwargs={"goal_id": other_goal.id})

        response = self.client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_check_goal_immediate_completion(self) -> None:
        today = timezone.localdate()
        one_day_goal = Goal.objects.create(
            user=self.user,
            title="즉시 완료",
            start_date=today,
            end_date=today,
            status=Status.IN_PROGRESS,
        )
        url = reverse("goal-check", kwargs={"goal_id": one_day_goal.id})

        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["progress_rate"] == 100

        one_day_goal.refresh_from_db()
        assert one_day_goal.status == Status.COMPLETED
