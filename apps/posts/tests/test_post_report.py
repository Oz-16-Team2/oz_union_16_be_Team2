import uuid
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.core.choices import ReportReasonType
from apps.posts.models import Post
from apps.reports.models import Report

User = get_user_model()

if TYPE_CHECKING:
    from apps.users.models import User as UserType
else:
    UserType = User


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db: None) -> UserType:
    return User.objects.create_user(
        email=f"user-{uuid.uuid4()}@test.com",
        password="password123",
        nickname=f"user-{uuid.uuid4()}",
    )


@pytest.fixture
def other_user(db: None) -> UserType:
    return User.objects.create_user(
        email=f"other-{uuid.uuid4()}@test.com",
        password="password123",
        nickname=f"other-{uuid.uuid4()}",
    )


@pytest.fixture
def post(db: None, other_user: UserType) -> Post:
    return Post.objects.create(
        title="test post",
        content="content",
        user=other_user,
    )


def get_url(post_id: int) -> str:
    return f"/api/v1/posts/{post_id}/reports/"


def authenticate(client: APIClient, user: UserType) -> None:
    client.force_authenticate(user=user)


@pytest.mark.django_db
def test_create_post_report_success(
    api_client: APIClient,
    user: UserType,
    post: Post,
) -> None:
    authenticate(api_client, user)

    res: Response = api_client.post(
        get_url(post.id),
        {
            "reason_type": ReportReasonType.SPAM,
            "reason_detail": "스팸입니다",
        },
    )

    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_duplicate_report(
    api_client: APIClient,
    user: UserType,
    post: Post,
) -> None:
    authenticate(api_client, user)

    Report.objects.create(
        user_id=user.id,
        target_id=post.id,
        target_type="POST",
        reason_type=ReportReasonType.SPAM,
        reason_detail="test",
        status="PENDING",
    )

    res: Response = api_client.post(
        get_url(post.id),
        {
            "reason_type": ReportReasonType.SPAM,
            "reason_detail": "again",
        },
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_post_not_found(
    api_client: APIClient,
    user: UserType,
) -> None:
    authenticate(api_client, user)

    res: Response = api_client.post(
        get_url(99999),
        {
            "reason_type": ReportReasonType.SPAM,
            "reason_detail": "test",
        },
    )

    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_validation_error_other_without_detail(
    api_client: APIClient,
    user: UserType,
    post: Post,
) -> None:
    authenticate(api_client, user)

    res: Response = api_client.post(
        get_url(post.id),
        {
            "reason_type": ReportReasonType.OTHER,
            "reason_detail": "",
        },
    )

    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_unauthorized(
    api_client: APIClient,
    post: Post,
) -> None:
    res: Response = api_client.post(
        get_url(post.id),
        {
            "reason_type": ReportReasonType.SPAM,
            "reason_detail": "test",
        },
    )

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
