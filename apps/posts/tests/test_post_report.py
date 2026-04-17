import uuid
from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.choices import ReportReasonType
from apps.posts.models import Post
from apps.reports.models import Report

User = get_user_model()


class PostReportAPITest(APITestCase):
    user: Any
    other_user: Any
    post: Any

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email=f"user-{uuid.uuid4()}@test.com",
            password="password123",
            nickname=f"user-{uuid.uuid4()}",
        )

        cls.other_user = User.objects.create_user(
            email=f"other-{uuid.uuid4()}@test.com",
            password="password123",
            nickname=f"other-{uuid.uuid4()}",
        )

        cls.post = Post.objects.create(
            title="test post",
            content="content",
            user=cls.other_user,
        )

    def get_url(self, post_id: int) -> str:
        return f"/api/v1/posts/{post_id}/reports/"

    def authenticate(self, user: Any) -> None:
        self.client.force_authenticate(user=user)

    def test_create_post_report_success(self) -> None:
        self.authenticate(self.user)

        res = self.client.post(
            self.get_url(self.post.id),
            {
                "reason_type": ReportReasonType.SPAM,
                "reason_detail": "스팸입니다",
            },
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_duplicate_report(self) -> None:
        self.authenticate(self.user)

        Report.objects.create(
            user_id=self.user.id,
            target_id=self.post.id,
            target_type="POST",
            reason_type=ReportReasonType.SPAM,
            reason_detail="test",
            status="PENDING",
        )

        res = self.client.post(
            self.get_url(self.post.id),
            {
                "reason_type": ReportReasonType.SPAM,
                "reason_detail": "again",
            },
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_not_found(self) -> None:
        self.authenticate(self.user)

        res = self.client.post(
            self.get_url(99999),
            {
                "reason_type": ReportReasonType.SPAM,
                "reason_detail": "test",
            },
        )

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_validation_error_other_without_detail(self) -> None:
        self.authenticate(self.user)

        res = self.client.post(
            self.get_url(self.post.id),
            {
                "reason_type": ReportReasonType.OTHER,
                "reason_detail": "",
            },
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized(self) -> None:
        res = self.client.post(
            self.get_url(self.post.id),
            {
                "reason_type": ReportReasonType.SPAM,
                "reason_detail": "test",
            },
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
