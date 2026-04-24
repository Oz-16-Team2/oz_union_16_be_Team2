from __future__ import annotations

import uuid
from typing import Any

import pytest
from django.test import Client

from apps.posts.models import Post
from apps.posts.tests.factories import PostFactory
from apps.users.models import User


@pytest.fixture
def admin_client(db: Any) -> Client:
    user = User.objects.create_superuser(
        email=f"admin_post_{uuid.uuid4().hex}@test.com",
        password="1234",
        is_active=True,
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def posts(db: Any) -> list[Post]:
    return PostFactory.create_batch(10)


@pytest.mark.django_db
class TestDjangoAdminPostViews:
    def test_post_list(self, admin_client: Client, posts: list[Post]) -> None:
        response = admin_client.get("/admin/posts/post/")
        assert response.status_code == 200

    def test_post_search_all(self, admin_client: Client, posts: list[Post]) -> None:
        response = admin_client.get("/admin/posts/post/?q=1")
        assert response.status_code == 200

    def test_post_search_by_post_id(self, admin_client: Client, posts: list[Post]) -> None:
        post = posts[0]
        response = admin_client.get(f"/admin/posts/post/?filter_type=post_id&q={post.id}")
        assert response.status_code == 200

    def test_post_search_by_user_id(self, admin_client: Client, posts: list[Post]) -> None:
        user_id = posts[0].user_id
        response = admin_client.get(f"/admin/posts/post/?filter_type=user_id&q={user_id}")
        assert response.status_code == 200
