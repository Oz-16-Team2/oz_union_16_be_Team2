from typing import Any
from unittest.mock import Mock, patch

import pytest
from django.test import override_settings
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.users.views.social_views import (
    GoogleSocialLoginAPIView,
    KakaoSocialLoginAPIView,
    NaverSocialLoginAPIView,
    _oauth_callback_url,
    _social_callback_login,
)


def test_oauth_callback_url(settings: Any) -> None:
    settings.BACKEND_BASE_URL = "http://backend.test/"

    result = _oauth_callback_url("google")

    assert result == "http://backend.test/api/v1/accounts/social-login/google/callback/"


@pytest.mark.django_db
@override_settings(
    FRONTEND_BASE_URL="http://frontend.test",
    BACKEND_BASE_URL="http://backend.test",
    COOKIE_SECURE=False,
    COOKIE_SAME_SITE="Lax",
)
@patch(
    "apps.users.views.social_views.google_social_login",
    return_value={"access_token": "access", "refresh_token": "refresh"},
)
def test_google_social_callback_success(mock_login: Mock) -> None:
    factory = APIRequestFactory()
    request = factory.get("/callback/", {"code": "google-code"})

    response = GoogleSocialLoginAPIView.as_view()(request)

    assert response.status_code == 302
    assert response["Location"] == "http://frontend.test"
    assert response.cookies["refresh_token"].value == "refresh"
    mock_login.assert_called_once()


@pytest.mark.django_db
@override_settings(
    FRONTEND_BASE_URL="http://frontend.test",
    BACKEND_BASE_URL="http://backend.test",
)
@patch(
    "apps.users.views.social_views.kakao_social_login",
    return_value={"access_token": "access", "refresh_token": "refresh"},
)
def test_kakao_social_callback_success(mock_login: Mock) -> None:
    factory = APIRequestFactory()
    request = factory.get("/callback/", {"code": "kakao-code"})

    response = KakaoSocialLoginAPIView.as_view()(request)

    assert response.status_code == 302
    assert response["Location"] == "http://frontend.test"
    assert response.cookies["refresh_token"].value == "refresh"
    mock_login.assert_called_once()


@pytest.mark.django_db
@override_settings(
    FRONTEND_BASE_URL="http://frontend.test",
    BACKEND_BASE_URL="http://backend.test",
)
@patch(
    "apps.users.views.social_views.naver_social_login",
    return_value={"access_token": "access", "refresh_token": "refresh"},
)
def test_naver_social_callback_success(mock_login: Mock) -> None:
    factory = APIRequestFactory()
    request = factory.get("/callback/", {"code": "naver-code", "state": "state"})

    response = NaverSocialLoginAPIView.as_view()(request)

    assert response.status_code == 302
    assert response["Location"] == "http://frontend.test"
    assert response.cookies["refresh_token"].value == "refresh"
    mock_login.assert_called_once()


def test_social_callback_requires_code() -> None:
    factory = APIRequestFactory()
    request = factory.get("/callback/")

    with pytest.raises(ValidationError):
        _social_callback_login(request, provider="google")


def test_naver_social_callback_requires_state() -> None:
    factory = APIRequestFactory()
    request = factory.get("/callback/", {"code": "naver-code"})

    with pytest.raises(ValidationError):
        _social_callback_login(request, provider="naver")


def test_social_callback_invalid_provider() -> None:
    factory = APIRequestFactory()
    request = factory.get("/callback/", {"code": "code"})

    with pytest.raises(ValidationError):
        _social_callback_login(request, provider="invalid")
