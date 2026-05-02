import pytest

from apps.users.serializers.auth_serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    TokenRefreshSerializer,
)


def test_login_serializer_normalizes_email() -> None:
    serializer = LoginSerializer(data={"email": " TEST@EXAMPLE.COM ", "password": "pass1234"})

    assert serializer.is_valid()
    assert serializer.validated_data["email"] == "test@example.com"


@pytest.mark.parametrize("serializer_class", [LogoutSerializer, TokenRefreshSerializer])
def test_refresh_token_required(serializer_class: type) -> None:
    serializer = serializer_class(data={})

    assert not serializer.is_valid()
    assert "refresh_token" in serializer.errors


@pytest.mark.parametrize("serializer_class", [LogoutSerializer, TokenRefreshSerializer])
def test_refresh_token_valid(serializer_class: type) -> None:
    serializer = serializer_class(data={"refresh_token": "token"})

    assert serializer.is_valid()


def test_change_password_success() -> None:
    serializer = ChangePasswordSerializer(
        data={
            "password": "oldpass123",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123",
        }
    )

    assert serializer.is_valid()


def test_change_password_requires_letter_and_number() -> None:
    serializer = ChangePasswordSerializer(
        data={
            "password": "oldpass123",
            "new_password": "abcdefgh",
            "new_password_confirm": "abcdefgh",
        }
    )

    assert not serializer.is_valid()
    assert "new_password" in serializer.errors


def test_change_password_confirm_mismatch() -> None:
    serializer = ChangePasswordSerializer(
        data={
            "password": "oldpass123",
            "new_password": "newpass123",
            "new_password_confirm": "otherpass123",
        }
    )

    assert not serializer.is_valid()
    assert "new_password_confirm" in serializer.errors
