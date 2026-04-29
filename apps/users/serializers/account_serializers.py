import re
from typing import Any

from rest_framework import serializers

from apps.core.choices import ProfileImageCode


class SignupSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    nickname = serializers.CharField(max_length=30)
    profile_image = serializers.ChoiceField(
        choices=ProfileImageCode.choices,
        required=False,
        default=ProfileImageCode.AVATAR_01,
    )
    email_token = serializers.CharField(required=True, max_length=1024)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def validate_nickname(self, value: str) -> str:
        return value.strip()

    def validate_password(self, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise serializers.ValidationError("비밀번호 형식이 올바르지 않습니다.")
        return value


class EmailVerificationSendSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class EmailVerificationVerifySerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=20)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class NicknameCheckSerializer(serializers.Serializer[Any]):
    nickname = serializers.CharField(max_length=30)

    def validate_nickname(self, value: str) -> str:
        return value.strip()
