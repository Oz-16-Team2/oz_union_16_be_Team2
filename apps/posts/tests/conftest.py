import uuid
from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.posts.models import Post


@pytest.fixture
def test_user(db: Any) -> Any:
    """
    포스트 테스트 전용 유저
    혹시 모를 충돌을 방지하기 위해 닉네임 뒤에 짧은 UUID를 붙이는 것이 실무 팁이라 함.
    다른 앱 테스트 데이터와 충돌할 가능성 0% ... 여야하는데 왜이럴까
    """
    User = get_user_model()
    unique_id = str(uuid.uuid4())[:8]
    return User.objects.create_user(
        email=f"post_test_{unique_id}@aaa.com", nickname=f"post_tester_{unique_id}", password="password123"
    )


@pytest.fixture
def test_post(db: Any, test_user: Any) -> Post:
    """포스트 테스트 전용 게시글입니다."""
    return Post.objects.create(user_id=test_user.id)
