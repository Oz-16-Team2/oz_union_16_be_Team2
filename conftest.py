from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.posts.models import Post
from apps.users.models import User


@pytest.fixture
def api_client() -> APIClient:
    """
    DRF API 요청을 위한 클라이언트 픽스처입니다.
    모든 API 테스트에서 인자로 주입받아 사용할 수 있습니다.
    """
    return APIClient()


@pytest.fixture
def test_user(db: Any) -> User:
    """
    테스트용 유저를 생성하는 픽스처입니다.
    db 인자를 통해 데이터베이스 접근 권한을 가집니다.
    """
    return User.objects.create_user(email="test@test.com", nickname="testuser", password="password123")


@pytest.fixture
def test_post(db: Any, test_user: User) -> Post:
    """
    테스트용 게시글을 생성하는 픽스처입니다.
    이미 생성된 test_user 픽스처를 주입받아 관계를 맺습니다.
    """
    post = Post.objects.create(user_id=test_user.id)
    return post
