from typing import Any
from unittest.mock import Mock, patch

import pytest
from rest_framework.exceptions import ValidationError

from apps.users.models import User
from apps.users.services.social_services import (
    _get_or_create_unique_nickname,
    _normalize_social_email,
    google_social_login,
    kakao_social_login,
    naver_social_login,
)


@pytest.mark.django_db
def test_get_or_create_unique_nickname_without_duplicate() -> None:
    assert _get_or_create_unique_nickname("tester") == "tester"


@pytest.mark.django_db
def test_get_or_create_unique_nickname_with_duplicate(user: Any) -> None:
    user.nickname = "tester"
    user.save(update_fields=["nickname"])

    nickname = _get_or_create_unique_nickname("tester")

    assert nickname != "tester"
    assert nickname.startswith("tester_")


def test_normalize_social_email_with_email() -> None:
    assert _normalize_social_email("google", "123", " TEST@EXAMPLE.COM ") == "test@example.com"


def test_normalize_social_email_without_email() -> None:
    assert _normalize_social_email("google", "123", None) == "google_123@social.local"


@pytest.mark.django_db
@patch(
    "apps.users.services.social_services._build_login_payload",
    return_value={"access_token": "access", "refresh_token": "refresh"},
)
@patch("apps.users.services.social_services._http_json")
def test_google_social_login_creates_user(
    mock_http_json: Mock,
    mock_payload: Mock,
) -> None:
    mock_http_json.side_effect = [
        {"access_token": "google-access-token"},
        {"sub": "google-id", "email": "google@example.com", "name": "GoogleUser"},
    ]

    result = google_social_login(code="code", redirect_uri="http://callback")

    assert result == {
        "access_token": "access",
        "refresh_token": "refresh",
    }
    assert User.objects.filter(email="google@example.com").exists()
    mock_payload.assert_called_once()


@pytest.mark.django_db
@patch(
    "apps.users.services.social_services._build_login_payload",
    return_value={"access_token": "access", "refresh_token": "refresh"},
)
@patch("apps.users.services.social_services._http_json")
def test_google_social_login_existing_user(
    mock_http_json: Mock,
    mock_payload: Mock,
    user: Any,
) -> None:
    user.email = "google@example.com"
    user.save(update_fields=["email"])

    mock_http_json.side_effect = [
        {"access_token": "google-access-token"},
        {"sub": "google-id", "email": "google@example.com", "name": "GoogleUser"},
    ]

    result = google_social_login(code="code", redirect_uri="http://callback")

    assert result["access_token"] == "access"
    mock_payload.assert_called_once()


@pytest.mark.django_db
@patch("apps.users.services.social_services._http_json", return_value={})
def test_google_social_login_without_access_token(mock_http_json: Mock) -> None:
    with pytest.raises(ValidationError):
        google_social_login(code="code", redirect_uri="http://callback")

    mock_http_json.assert_called_once()


@pytest.mark.django_db
@patch(
    "apps.users.services.social_services._build_login_payload",
    return_value={"access_token": "access", "refresh_token": "refresh"},
)
@patch("apps.users.services.social_services._http_json")
def test_naver_social_login_success(
    mock_http_json: Mock,
    mock_payload: Mock,
) -> None:
    mock_http_json.side_effect = [
        {"access_token": "naver-access-token"},
        {
            "response": {
                "id": "naver-id",
                "email": "naver@example.com",
                "nickname": "NaverUser",
            }
        },
    ]

    result = naver_social_login(code="code", redirect_uri="http://callback", state="state")

    assert result["refresh_token"] == "refresh"
    assert User.objects.filter(email="naver@example.com").exists()
    mock_payload.assert_called_once()


def test_naver_social_login_requires_state() -> None:
    with pytest.raises(ValidationError):
        naver_social_login(code="code", redirect_uri="http://callback", state="")


@pytest.mark.django_db
@patch("apps.users.services.social_services._http_json", return_value={})
def test_naver_social_login_without_access_token(mock_http_json: Mock) -> None:
    with pytest.raises(ValidationError):
        naver_social_login(code="code", redirect_uri="http://callback", state="state")

    mock_http_json.assert_called_once()


@pytest.mark.django_db
@patch(
    "apps.users.services.social_services._build_login_payload",
    return_value={"access_token": "access", "refresh_token": "refresh"},
)
@patch("apps.users.services.social_services._http_json")
def test_kakao_social_login_success(
    mock_http_json: Mock,
    mock_payload: Mock,
) -> None:
    mock_http_json.side_effect = [
        {"access_token": "kakao-access-token"},
        {
            "id": 12345,
            "kakao_account": {
                "email": "kakao@example.com",
                "profile": {"nickname": "KakaoUser"},
            },
        },
    ]

    result = kakao_social_login(code="code", redirect_uri="http://callback")

    assert result["access_token"] == "access"
    assert User.objects.filter(email="kakao@example.com").exists()
    mock_payload.assert_called_once()


@pytest.mark.django_db
@patch("apps.users.services.social_services._http_json", return_value={})
def test_kakao_social_login_without_access_token(mock_http_json: Mock) -> None:
    with pytest.raises(ValidationError):
        kakao_social_login(code="code", redirect_uri="http://callback")

    mock_http_json.assert_called_once()
