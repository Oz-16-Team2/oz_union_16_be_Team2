from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.services.user_services import generate_email_token

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    client = APIClient()
    client.raise_request_exception = False
    return client


@pytest.fixture
def password() -> str:
    return "testpass123!"


@pytest.fixture
def user(password: str) -> Any:
    return User.objects.create_user(
        email="test@example.com",
        password=password,
        nickname="tester",
        profile_image="avatar_1",
    )


@pytest.fixture
def signup_url() -> str:
    return reverse("signup")


@pytest.fixture
def nickname_check_url() -> str:
    return reverse("check-nickname")


@pytest.fixture
def login_url() -> str:
    return reverse("login")


@pytest.fixture
def logout_url() -> str:
    return reverse("logout")


@pytest.fixture
def token_refresh_url() -> str:
    return reverse("token-refresh")


@pytest.fixture
def change_password_url() -> str:
    return reverse("change-password")


@pytest.mark.django_db
def test_signup_success(api_client: APIClient, signup_url: str) -> None:
    email = "newuser@example.com"

    payload = {
        "email": email,
        "password": "newpass123!",
        "nickname": "newtester",
        "profile_image": "avatar_1",
        "email_token": generate_email_token(email),
    }

    response = api_client.post(signup_url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"detail": "회원가입이 완료되었습니다."}
    assert User.objects.filter(email="newuser@example.com").exists()


@pytest.mark.django_db
def test_signup_duplicate_email(
    api_client: APIClient,
    signup_url: str,
    user: Any,
) -> None:
    email = "test@example.com"

    payload = {
        "email": email,
        "password": "newpass123!",
        "nickname": "anothernick",
        "profile_image": "avatar_1",
        "email_token": generate_email_token(email),
    }

    response = api_client.post(signup_url, payload, format="json")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "error_detail": {
            "email": ["이미 가입된 이메일입니다."],
        }
    }


@pytest.mark.django_db
def test_signup_duplicate_nickname(
    api_client: APIClient,
    signup_url: str,
    user: Any,
) -> None:
    email = "another@example.com"

    payload = {
        "email": email,
        "password": "newpass123!",
        "nickname": "tester",
        "profile_image": "avatar_1",
        "email_token": generate_email_token(email),
    }

    response = api_client.post(signup_url, payload, format="json")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "error_detail": {
            "nickname": ["이미 사용 중인 닉네임입니다."],
        }
    }


@pytest.mark.django_db
def test_check_nickname_success(
    api_client: APIClient,
    nickname_check_url: str,
) -> None:
    response = api_client.get(
        nickname_check_url,
        {"nickname": "available_nick"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "사용가능한 닉네임입니다."}


@pytest.mark.django_db
def test_check_nickname_conflict(
    api_client: APIClient,
    nickname_check_url: str,
    user: Any,
) -> None:
    response = api_client.get(
        nickname_check_url,
        {"nickname": "tester"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "error_detail": {
            "nickname": ["이미 사용 중인 닉네임입니다."],
        }
    }


@pytest.mark.django_db
def test_login_success(
    api_client: APIClient,
    login_url: str,
    user: Any,
    password: str,
) -> None:
    payload = {
        "email": "test@example.com",
        "password": password,
    }

    response = api_client.post(login_url, payload, format="json")
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in body
    assert "refresh_token" not in body
    assert "refresh_token" in response.cookies


@pytest.mark.django_db
def test_login_fail_invalid_password(
    api_client: APIClient,
    login_url: str,
    user: Any,
) -> None:
    payload = {
        "email": "test@example.com",
        "password": "wrong-password",
    }

    response = api_client.post(login_url, payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "error_detail": "이메일 또는 비밀번호가 올바르지 않습니다.",
    }


@pytest.mark.django_db
def test_token_refresh_success(
    api_client: APIClient,
    login_url: str,
    token_refresh_url: str,
    user: Any,
    password: str,
) -> None:
    login_response = api_client.post(
        login_url,
        {"email": "test@example.com", "password": password},
        format="json",
    )
    refresh_token = login_response.cookies["refresh_token"].value

    response = api_client.post(
        token_refresh_url,
        {"refresh_token": refresh_token},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


@pytest.mark.django_db
def test_token_refresh_fail_missing_token(
    api_client: APIClient,
    token_refresh_url: str,
) -> None:
    response = api_client.post(token_refresh_url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "error_detail": {
            "refresh_token": ["이 필드는 필수 항목입니다."],
        }
    }


@pytest.mark.django_db
def test_logout_success(
    api_client: APIClient,
    login_url: str,
    logout_url: str,
    user: Any,
    password: str,
) -> None:
    login_response = api_client.post(
        login_url,
        {"email": "test@example.com", "password": password},
        format="json",
    )
    refresh_token = login_response.cookies["refresh_token"].value

    api_client.cookies["refresh_token"] = refresh_token
    response = api_client.post(logout_url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "로그아웃 되었습니다."}


@pytest.mark.django_db
def test_logout_success_without_cookie(
    api_client: APIClient,
    logout_url: str,
) -> None:
    response = api_client.post(logout_url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "로그아웃 되었습니다."}


@pytest.mark.django_db
def test_change_password_success(
    api_client: APIClient,
    login_url: str,
    change_password_url: str,
    user: Any,
    password: str,
) -> None:
    login_response = api_client.post(
        login_url,
        {"email": "test@example.com", "password": password},
        format="json",
    )
    access_token = login_response.json()["access_token"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    payload = {
        "password": password,
        "new_password": "changedpass123!",
        "new_password_confirm": "changedpass123!",
    }

    response = api_client.patch(change_password_url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "비밀번호가 변경되었습니다."}

    user.refresh_from_db()
    assert user.check_password("changedpass123!")


@pytest.mark.django_db
def test_change_password_fail_wrong_current_password(
    api_client: APIClient,
    login_url: str,
    change_password_url: str,
    user: Any,
    password: str,
) -> None:
    login_response = api_client.post(
        login_url,
        {"email": "test@example.com", "password": password},
        format="json",
    )
    access_token = login_response.json()["access_token"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    payload = {
        "password": "wrong-password",
        "new_password": "changedpass123!",
        "new_password_confirm": "changedpass123!",
    }

    response = api_client.patch(change_password_url, payload, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "error_detail": "기존 비밀번호가 일치하지 않습니다.",
    }


@pytest.mark.django_db
def test_change_password_fail_unauthorized(
    api_client: APIClient,
    change_password_url: str,
    password: str,
) -> None:
    payload = {
        "password": password,
        "new_password": "changedpass123!",
        "new_password_confirm": "changedpass123!",
    }

    response = api_client.patch(change_password_url, payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_change_password_fail_password_confirm_mismatch(
    api_client: APIClient,
    login_url: str,
    change_password_url: str,
    user: Any,
    password: str,
) -> None:
    login_response = api_client.post(
        login_url,
        {"email": "test@example.com", "password": password},
        format="json",
    )
    access_token = login_response.json()["access_token"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    payload = {
        "password": password,
        "new_password": "changedpass123!",
        "new_password_confirm": "differentpass123!",
    }

    response = api_client.patch(change_password_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "error_detail": {
            "new_password_confirm": ["비밀번호가 일치하지 않습니다."],
        }
    }
