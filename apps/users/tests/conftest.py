from typing import Any

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    client = APIClient()
    client.raise_request_exception = False
    return client


@pytest.fixture(autouse=True)
def apply_exception_handler(settings: Any) -> None:
    settings.REST_FRAMEWORK["EXCEPTION_HANDLER"] = "apps.core.exception_handler.custom_exception_handler"
