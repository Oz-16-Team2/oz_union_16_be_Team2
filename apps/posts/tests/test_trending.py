"""
인기 게시글 조회 API 테스트 (GET /api/v1/posts/trending).

검증 항목:
- 정상 응답 구조 (posts / page / size / total_count)
- period=week / period=day 필터링
- 좋아요 수 내림차순 정렬
- 기간 밖 게시글 미포함
- 비공개 게시글 미포함
- 삭제된 게시글 미포함
- 미인증 요청 401
- 잘못된 period 값 400
"""

from __future__ import annotations

import datetime
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Post, PostLike
from apps.posts.tests.factories import PostFactory_create, UserFactory_create

User = get_user_model()

TRENDING_URL = "/api/v1/posts/trending"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db: None) -> User:  # type: ignore[valid-type]
    return UserFactory_create()


def auth(client: APIClient, u: User) -> None:  # type: ignore[valid-type]
    client.force_authenticate(user=u)


def _like(post: Post, n: int) -> None:
    """게시글에 n명이 좋아요를 누름."""
    for _ in range(n):
        liker = UserFactory_create()
        PostLike.objects.get_or_create(post=post, user=liker)


# ============================================================
# 정상 케이스
# ============================================================


def _posts(res: Any) -> list[Any]:
    return list(res.json()["detail"]["posts"])


def _data(res: Any) -> Any:
    return res.json()["detail"]


@pytest.mark.django_db
def test_trending_returns_200_with_correct_schema(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    auth(api_client, user)
    PostFactory_create()

    res = api_client.get(TRENDING_URL)

    assert res.status_code == status.HTTP_200_OK
    detail = _data(res)
    assert "posts" in detail
    assert "page" in detail
    assert "size" in detail
    assert "total_count" in detail


@pytest.mark.django_db
@freeze_time("2026-04-24 12:00:00")
def test_trending_week_hot_score_favors_newer_post(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    """새 글(좋아요 적음)이 오래된 글(좋아요 많음)보다 Hot Score가 높아야 한다.
    오래된 글: 좋아요 20개, 6일 전 작성 → score ≈ 20 / (144+2)^1.7 ≈ 0.077
    새 글:     좋아요 5개,  1시간 전 작성 → score ≈  5 / (1+2)^1.7  ≈ 1.14
    """
    auth(api_client, user)

    old_post = PostFactory_create()
    Post.objects.filter(pk=old_post.pk).update(created_at=timezone.now() - datetime.timedelta(days=6))
    _like(old_post, 20)

    new_post = PostFactory_create()
    Post.objects.filter(pk=new_post.pk).update(created_at=timezone.now() - datetime.timedelta(hours=1))
    _like(new_post, 5)

    res = api_client.get(TRENDING_URL, {"period": "week", "size": "10"})

    assert res.status_code == status.HTTP_200_OK
    post_ids = [p["post_id"] for p in _posts(res)]
    assert post_ids.index(new_post.id) < post_ids.index(old_post.id)


@pytest.mark.django_db
def test_trending_sorted_by_like_count_desc(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    """나이 차이가 거의 없을 때 좋아요 많은 글이 앞에 와야 한다."""
    auth(api_client, user)

    low = PostFactory_create()
    high = PostFactory_create()
    _like(low, 2)
    _like(high, 10)

    res = api_client.get(TRENDING_URL, {"period": "week", "size": "10"})

    assert res.status_code == status.HTTP_200_OK
    post_ids = [p["post_id"] for p in _posts(res)]
    assert post_ids.index(high.id) < post_ids.index(low.id)


@pytest.mark.django_db
@freeze_time("2026-04-24 12:00:00")
def test_trending_week_excludes_older_posts(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    """7일 초과 게시글은 week 결과에 포함되지 않는다."""
    auth(api_client, user)

    recent = PostFactory_create()
    old = PostFactory_create()
    Post.objects.filter(pk=old.pk).update(created_at=timezone.now() - datetime.timedelta(days=8))

    res = api_client.get(TRENDING_URL, {"period": "week", "size": "10"})

    post_ids = [p["post_id"] for p in _posts(res)]
    assert recent.id in post_ids
    assert old.id not in post_ids


@pytest.mark.django_db
@freeze_time("2026-04-24 12:00:00")
def test_trending_day_excludes_posts_older_than_24h(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    """24시간 초과 게시글은 day 결과에 포함되지 않는다."""
    auth(api_client, user)

    recent = PostFactory_create()
    old = PostFactory_create()
    Post.objects.filter(pk=old.pk).update(created_at=timezone.now() - datetime.timedelta(hours=25))

    res = api_client.get(TRENDING_URL, {"period": "day", "size": "10"})

    post_ids = [p["post_id"] for p in _posts(res)]
    assert recent.id in post_ids
    assert old.id not in post_ids


@pytest.mark.django_db
def test_trending_excludes_private_posts(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    """비공개 게시글은 결과에 포함되지 않는다."""
    auth(api_client, user)

    public = PostFactory_create()
    private = PostFactory_create(is_private=True)

    res = api_client.get(TRENDING_URL, {"size": "50"})

    post_ids = [p["post_id"] for p in _posts(res)]
    assert public.id in post_ids
    assert private.id not in post_ids


@pytest.mark.django_db
def test_trending_excludes_deleted_posts(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    """삭제된 게시글은 결과에 포함되지 않는다."""
    auth(api_client, user)

    alive = PostFactory_create()
    dead = PostFactory_create()
    Post.objects.filter(pk=dead.pk).update(deleted_at=timezone.now())

    res = api_client.get(TRENDING_URL, {"size": "50"})

    post_ids = [p["post_id"] for p in _posts(res)]
    assert alive.id in post_ids
    assert dead.id not in post_ids


@pytest.mark.django_db
def test_trending_pagination(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    """size=2로 페이지네이션 시 2개만 반환되고 total_count는 전체 수를 반영한다."""
    auth(api_client, user)

    for _ in range(5):
        PostFactory_create()

    res = api_client.get(TRENDING_URL, {"size": "2", "page": "0"})

    detail = _data(res)
    assert len(detail["posts"]) == 2
    assert detail["total_count"] >= 5


@pytest.mark.django_db
def test_trending_response_item_fields(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    """응답 아이템에 필요한 모든 필드가 포함된다."""
    auth(api_client, user)
    PostFactory_create()

    res = api_client.get(TRENDING_URL)

    item = _posts(res)[0]
    for field in (
        "post_id",
        "images",
        "profile_image_url",
        "nickname",
        "created_at",
        "title",
        "tags",
        "content_preview",
        "like_count",
        "comment_count",
        "is_liked",
        "is_scrapped",
    ):
        assert field in item, f"응답에 '{field}' 필드가 없습니다"


# ============================================================
# 에러 케이스
# ============================================================


@pytest.mark.django_db
def test_trending_unauthenticated_returns_200(api_client: APIClient) -> None:
    res = api_client.get(TRENDING_URL)
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_trending_invalid_period_returns_400(api_client: APIClient, user: User) -> None:  # type: ignore[valid-type]
    auth(api_client, user)
    res = api_client.get(TRENDING_URL, {"period": "invalid_value"})
    assert res.status_code == status.HTTP_400_BAD_REQUEST
