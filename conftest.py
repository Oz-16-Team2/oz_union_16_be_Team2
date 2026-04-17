import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """
    DRF API 요청을 위한 클라이언트 픽스처입니다.
    모든 API 테스트에서 인자로 주입받아 사용할 수 있습니다.
    """
    return APIClient()
