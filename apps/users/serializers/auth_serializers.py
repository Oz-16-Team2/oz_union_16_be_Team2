import re
from typing import Any

from rest_framework import serializers


class LoginSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class LogoutSerializer(serializers.Serializer[Any]):
    refresh_token = serializers.CharField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs.get("refresh_token"):
            raise serializers.ValidationError({"refresh_token": ["이 필드는 필수 항목입니다."]})
        return attrs


class TokenRefreshSerializer(serializers.Serializer[Any]):
    refresh_token = serializers.CharField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs.get("refresh_token"):
            raise serializers.ValidationError({"refresh_token": ["이 필드는 필수 항목입니다."]})
        return attrs


class ChangePasswordSerializer(serializers.Serializer[Any]):
    password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "min_length": "비밀번호 형식이 올바르지 않습니다.",
            "required": "이 필드는 필수 항목입니다.",
        },
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "min_length": "비밀번호 형식이 올바르지 않습니다.",
            "required": "이 필드는 필수 항목입니다.",
        },
    )

    def validate_new_password(self, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise serializers.ValidationError("비밀번호 형식이 올바르지 않습니다.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["비밀번호가 일치하지 않습니다."]})
        return attrs
