from __future__ import annotations

from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Tag
from apps.users.models import User


class AdminTagAPIViewTest(APITestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="test1234",
            nickname="admin_user",
            is_staff=True,
        )
        self.normal_user = User.objects.create_user(
            email="user@test.com",
            password="test1234",
            nickname="normal_user",
            is_staff=False,
        )

    def test_admin_can_get_tags(self) -> None:
        Tag.objects.create(name="운동", is_active=True)
        Tag.objects.create(name="공부", is_active=False)

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(
            "/api/v1/admin/tags",
            {"page": 1, "size": 10},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(len(response.data["detail"]), 2)

    def test_get_tags_returns_400_when_query_is_invalid(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(
            "/api/v1/admin/tags",
            {"page": 0, "size": 10},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "잘못된 요청입니다.")

    def test_get_tags_returns_401_when_unauthenticated(self) -> None:
        response = self.client.get(
            "/api/v1/admin/tags",
            {"page": 1, "size": 10},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "관리자 인증이 필요합니다.")

    def test_get_tags_returns_403_when_not_admin(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(
            "/api/v1/admin/tags",
            {"page": 1, "size": 10},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")

    def test_admin_can_create_tag(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/v1/admin/tags",
            {"name": "운동"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["detail"], "태그가 생성되었습니다.")
        self.assertTrue(Tag.objects.filter(name="운동").exists())

    def test_create_tag_returns_400_when_name_is_missing(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/v1/admin/tags",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "잘못된 요청입니다.")

    def test_create_tag_returns_401_when_unauthenticated(self) -> None:
        response = self.client.post(
            "/api/v1/admin/tags",
            {"name": "운동"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "관리자 인증이 필요합니다.")

    def test_create_tag_returns_403_when_not_admin(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.post(
            "/api/v1/admin/tags",
            {"name": "운동"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")

    def test_create_tag_returns_409_when_name_already_exists(self) -> None:
        Tag.objects.create(name="운동", is_active=True)
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/api/v1/admin/tags",
            {"name": "운동"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error_detail"], "이미 존재하는 태그입니다.")

    def test_admin_can_update_tag_status(self) -> None:
        tag = Tag.objects.create(name="운동", is_active=True)
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            f"/api/v1/admin/tags/{tag.id}",
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "태그 상태가 수정되었습니다.")

        tag.refresh_from_db()
        self.assertFalse(tag.is_active)

    def test_update_tag_status_returns_400_when_is_active_is_missing(self) -> None:
        tag = Tag.objects.create(name="운동", is_active=True)
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            f"/api/v1/admin/tags/{tag.id}",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "잘못된 요청입니다.")

    def test_update_tag_status_returns_401_when_unauthenticated(self) -> None:
        tag = Tag.objects.create(name="운동", is_active=True)

        response = self.client.patch(
            f"/api/v1/admin/tags/{tag.id}",
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "관리자 인증이 필요합니다.")

    def test_update_tag_status_returns_403_when_not_admin(self) -> None:
        tag = Tag.objects.create(name="운동", is_active=True)
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.patch(
            f"/api/v1/admin/tags/{tag.id}",
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")

    def test_update_tag_status_returns_404_when_tag_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            "/api/v1/admin/tags/99999",
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "태그를 찾을 수 없습니다.")