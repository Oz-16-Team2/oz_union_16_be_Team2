from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.fixture
def api_client() -> APIClient:
    client = APIClient()
    client.raise_request_exception = False
    return client


@pytest.fixture(autouse=True)
def apply_exception_handler(settings: Any) -> None:
    settings.REST_FRAMEWORK["EXCEPTION_HANDLER"] = "apps.core.exception_handler.custom_exception_handler"


@pytest.fixture
def user(db: Any) -> User:
    return User.objects.create_user(
        email="test@example.com",
        password="pass1234",
        nickname="tester",
        profile_image="avatar_1",
    )
