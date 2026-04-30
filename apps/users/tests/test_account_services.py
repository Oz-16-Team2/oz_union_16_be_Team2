from typing import Any
from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from apps.core.exceptions import ConflictException
from apps.users.services.account_services import (
    check_nickname,
    generate_email_token,
    is_token_used,
    mark_token_used,
    send_email_verification_code,
    signup_user,
    verify_email,
    verify_email_token,
)


@pytest.mark.django_db
def test_check_nickname_success() -> None:
    result = check_nickname(nickname="newnick")

    assert result == {"detail": "사용가능한 닉네임입니다."}


@pytest.mark.django_db
def test_check_nickname_conflict(user: Any) -> None:
    with pytest.raises(ConflictException):
        check_nickname(nickname=user.nickname)


@pytest.mark.django_db
@patch("apps.users.services.account_services.send_mail")
@patch("apps.users.services.account_services.random.randint", return_value=123456)
def test_send_email_verification_code_success(
    mock_randint: Mock,
    mock_send_mail: Mock,
    settings: Any,
) -> None:
    settings.EMAIL_VERIFICATION_TIMEOUT = 300
    settings.DEFAULT_FROM_EMAIL = "admin@example.com"

    result = send_email_verification_code(email=" TEST@EXAMPLE.COM ")

    assert result == {"detail": "이메일 인증 코드가 전송되었습니다."}
    assert cache.get("email_code:test@example.com") == "123456"
    mock_randint.assert_called_once_with(100000, 999999)
    mock_send_mail.assert_called_once()


@pytest.mark.django_db
def test_send_email_verification_code_conflict(user: Any) -> None:
    with pytest.raises(ConflictException):
        send_email_verification_code(email=user.email)


def test_verify_email_success() -> None:
    cache.set("email_code:test@example.com", "123456", timeout=300)

    result = verify_email(email="TEST@EXAMPLE.COM", code="123456")

    assert result["detail"] == "이메일 인증에 성공하였습니다."
    assert "email_token" in result
    assert cache.get("email_code:test@example.com") is None


def test_verify_email_expired() -> None:
    with pytest.raises(ValidationError):
        verify_email(email="test@example.com", code="123456")


def test_verify_email_wrong_code() -> None:
    cache.set("email_code:test@example.com", "123456", timeout=300)

    with pytest.raises(ValidationError):
        verify_email(email="test@example.com", code="000000")


def test_generate_and_verify_email_token() -> None:
    token = generate_email_token("test@example.com")

    assert verify_email_token(token) == "test@example.com"


def test_verify_email_token_invalid() -> None:
    with pytest.raises(ValueError):
        verify_email_token("invalid-token")


def test_mark_token_used() -> None:
    token = "used-token"

    assert not is_token_used(token)

    mark_token_used(token)

    assert is_token_used(token)


@pytest.mark.django_db
def test_signup_user_success() -> None:
    email = "new@example.com"
    token = generate_email_token(email)

    result = signup_user(
        email=email,
        password="pass1234",
        nickname="newnick",
        profile_image="avatar_1",
        email_token=token,
    )

    assert result == {"detail": "회원가입이 완료되었습니다."}
    assert is_token_used(token)


@pytest.mark.django_db
def test_signup_user_requires_email_token() -> None:
    with pytest.raises(ValidationError):
        signup_user(
            email="new@example.com",
            password="pass1234",
            nickname="newnick",
            profile_image="avatar_1",
            email_token="",
        )


@pytest.mark.django_db
def test_signup_user_email_mismatch() -> None:
    token = generate_email_token("other@example.com")

    with pytest.raises(ValidationError):
        signup_user(
            email="new@example.com",
            password="pass1234",
            nickname="newnick",
            profile_image="avatar_1",
            email_token=token,
        )


@pytest.mark.django_db
def test_signup_user_used_token() -> None:
    token = generate_email_token("new@example.com")
    mark_token_used(token)

    with pytest.raises(ValidationError):
        signup_user(
            email="new@example.com",
            password="pass1234",
            nickname="newnick",
            profile_image="avatar_1",
            email_token=token,
        )


@pytest.mark.django_db
def test_signup_user_conflict(user: Any) -> None:
    token = generate_email_token(user.email)

    with pytest.raises(ConflictException):
        signup_user(
            email=user.email,
            password="pass1234",
            nickname=user.nickname,
            profile_image="avatar_1",
            email_token=token,
        )
