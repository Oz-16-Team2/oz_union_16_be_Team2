from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.goals.models import Goal
from apps.users.models import User


class GoalAPITestCase(APITestCase):
    user: User
    goal: Goal
    list_create_url: str
    detail_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(nickname="testuser", email="test@test.com", password="password123")
        cls.goal = Goal.objects.create(user=cls.user, title="기존 목표", start_date="2026-04-14", end_date="2026-05-14")
        cls.list_create_url = reverse("goal-create")
        cls.detail_url = reverse("goal-detail", kwargs={"goal_id": cls.goal.id})

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

    def test_create_goal_success(self) -> None:
        data = {"title": "새로운 운동 목표", "start_date": "2026-04-15", "end_date": "2026-05-15"}
        response = self.client.post(self.list_create_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "새로운 운동 목표")
        self.assertIn("progress_rate", response.data)

    def test_create_goal_date_validation_fail(self) -> None:
        data = {"title": "날짜 오류 목표", "start_date": "2026-04-15", "end_date": "2026-04-10"}
        response = self.client.post(self.list_create_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_date", response.data["error_detail"])

    def test_get_goal_list(self) -> None:
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_goal_detail(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["goal_id"], self.goal.id)

    def test_update_goal_success(self) -> None:
        data = {"title": "수정된 목표 제목"}
        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 목표 제목")

    def test_delete_goal_success(self) -> None:
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Goal.objects.filter(id=self.goal.id).exists())
