from __future__ import annotations

from typing import Any

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Tag
from apps.users.models import User


@pytest.fixture
def admin_tag_data() -> dict[str, Any]:
    admin_user = User.objects.create_user(
        email="admin_tag@test.com",
        password="test1234",
        nickname="admin_tag_user",
        is_staff=True,
    )
    normal_user = User.objects.create_user(
        email="user_tag@test.com",
        password="test1234",
        nickname="normal_tag_user",
        is_staff=False,
    )

    active_tag = Tag.objects.create(name="운동", is_active=True)
    inactive_tag = Tag.objects.create(name="공부", is_active=False)

    return {
        "admin_user": admin_user,
        "normal_user": normal_user,
        "active_tag": active_tag,
        "inactive_tag": inactive_tag,
    }


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_client(api_client: APIClient, admin_tag_data: dict[str, Any]) -> APIClient:
    api_client.force_authenticate(user=admin_tag_data["admin_user"])
    return api_client


@pytest.mark.django_db
class TestAdminTagAPIView:
    def test_admin_can_get_tags(self, admin_client: APIClient) -> None:
        response = admin_client.get(
            "/api/v1/admin/tags",
            {"page": 1, "size": 10},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data

        tag_names = [tag["name"] for tag in response.data["detail"]]
        assert "운동" in tag_names
        assert "공부" in tag_names

    def test_get_tags_returns_400_when_query_is_invalid(self, admin_client: APIClient) -> None:
        response = admin_client.get(
            "/api/v1/admin/tags",
            {"page": 0, "size": 10},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error_detail"] == "잘못된 요청입니다."

    def test_get_tags_returns_401_when_unauthenticated(self, api_client: APIClient) -> None:
        response = api_client.get(
            "/api/v1/admin/tags",
            {"page": 1, "size": 10},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error_detail"] == "관리자 인증이 필요합니다."

    def test_get_tags_returns_403_when_not_admin(self, api_client: APIClient, admin_tag_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=admin_tag_data["normal_user"])

        response = api_client.get(
            "/api/v1/admin/tags",
            {"page": 1, "size": 10},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error_detail"] == "권한이 없습니다."

    def test_admin_can_create_tag(self, admin_client: APIClient) -> None:
        response = admin_client.post(
            "/api/v1/admin/tags",
            {"name": "새태그"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["detail"] == "태그가 생성되었습니다."
        assert Tag.objects.filter(name="새태그").exists()

    def test_create_tag_returns_400_when_name_is_missing(self, admin_client: APIClient) -> None:
        response = admin_client.post(
            "/api/v1/admin/tags",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error_detail"] == "잘못된 요청입니다."

    def test_create_tag_returns_401_when_unauthenticated(self, api_client: APIClient) -> None:
        response = api_client.post(
            "/api/v1/admin/tags",
            {"name": "운동"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error_detail"] == "관리자 인증이 필요합니다."

    def test_create_tag_returns_403_when_not_admin(self, api_client: APIClient, admin_tag_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=admin_tag_data["normal_user"])

        response = api_client.post(
            "/api/v1/admin/tags",
            {"name": "운동"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error_detail"] == "권한이 없습니다."

    def test_create_tag_returns_409_when_name_already_exists(self, admin_client: APIClient) -> None:
        response = admin_client.post(
            "/api/v1/admin/tags",
            {"name": "운동"},
            format="json",
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["error_detail"] == "이미 존재하는 태그입니다."

    def test_admin_can_update_tag_status(self, admin_client: APIClient, admin_tag_data: dict[str, Any]) -> None:
        response = admin_client.patch(
            f"/api/v1/admin/tags/{admin_tag_data['active_tag'].id}",
            {"is_active": False},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "태그 상태가 수정되었습니다."

    def test_update_tag_status_returns_400_when_is_active_is_missing(
        self,
        admin_client: APIClient,
        admin_tag_data: dict[str, Any],
    ) -> None:
        response = admin_client.patch(
            f"/api/v1/admin/tags/{admin_tag_data['active_tag'].id}",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error_detail"] == "잘못된 요청입니다."

    def test_update_tag_status_returns_401_when_unauthenticated(
        self,
        api_client: APIClient,
        admin_tag_data: dict[str, Any],
    ) -> None:
        response = api_client.patch(
            f"/api/v1/admin/tags/{admin_tag_data['active_tag'].id}",
            {"is_active": False},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error_detail"] == "관리자 인증이 필요합니다."

    def test_update_tag_status_returns_403_when_not_admin(
        self,
        api_client: APIClient,
        admin_tag_data: dict[str, Any],
    ) -> None:
        api_client.force_authenticate(user=admin_tag_data["normal_user"])

        response = api_client.patch(
            f"/api/v1/admin/tags/{admin_tag_data['active_tag'].id}",
            {"is_active": False},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error_detail"] == "권한이 없습니다."

    def test_update_tag_status_returns_404_when_tag_not_found(self, admin_client: APIClient) -> None:
        response = admin_client.patch(
            "/api/v1/admin/tags/99999",
            {"is_active": False},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error_detail"] == "태그를 찾을 수 없습니다."