from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.goals.models import Goal
from apps.users.models import User


class GoalCheckAPITestCase(APITestCase):
    user: User
    goal: Goal
    check_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(nickname="checkuser", email="check@test.com", password="password123")
        cls.goal = Goal.objects.create(
            user=cls.user, title="매일 운동하기", start_date="2026-04-14", end_date="2026-05-14"
        )
        cls.check_url = reverse("goal-check", kwargs={"goal_id": cls.goal.id})

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_check_goal_success(self) -> None:
        response = self.client.post(self.check_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "오늘의 목표 달성 인증이 완료되었습니다.")
        self.assertEqual(response.data["goal_id"], self.goal.id)
        self.assertGreater(response.data["progress_rate"], 0)

    def test_check_goal_already_checked_fail(self) -> None:
        self.client.post(self.check_url)

        response = self.client.post(self.check_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"]["detail"][0], "오늘 이미 인증을 완료했습니다.")

    def test_check_goal_invalid_date_fail(self) -> None:
        past_goal = Goal.objects.create(
            user=self.user, title="과거의 목표", start_date="2020-01-01", end_date="2020-01-10"
        )
        url = reverse("goal-check", kwargs={"goal_id": past_goal.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"]["detail"][0], "목표 기간이 아닙니다.")

    def test_check_goal_not_found_fail(self) -> None:
        other_user = User.objects.create_user(nickname="other", email="other@test.com", password="password")
        other_goal = Goal.objects.create(
            user=other_user, title="남의 목표", start_date="2026-04-14", end_date="2026-05-14"
        )
        url = reverse("goal-check", kwargs={"goal_id": other_goal.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
