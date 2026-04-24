from typing import Any

from rest_framework import serializers

from apps.core.choices import ProfileImageCode
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User


class MessageResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer[Any]):
    access_token = serializers.CharField()


class EmailVerificationSuccessSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()
    email_token = serializers.CharField()


class ErrorDetailFieldListSerializer(serializers.Serializer[Any]):
    error_detail = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))


class ErrorDetailStringSerializer(serializers.Serializer[Any]):
    error_detail = serializers.CharField()


class WithdrawnAccountErrorDetailSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()
    expire_at = serializers.CharField()


class ErrorDetailWithdrawnSerializer(serializers.Serializer[Any]):
    error_detail = WithdrawnAccountErrorDetailSerializer()


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


class EmailVerificationSendSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()


class EmailVerificationVerifySerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=20)


class LoginSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


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


class NicknameCheckSerializer(serializers.Serializer[Any]):
    nickname = serializers.CharField(max_length=30)


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

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["비밀번호가 일치하지 않습니다."]})
        return attrs


class UserProfileSerializer(serializers.ModelSerializer[Any]):
    profile_img_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "nickname", "profile_img_url"]

    def get_profile_img_url(self, obj: User) -> str:
        return PROFILE_IMAGE_URL_MAP.get(obj.profile_image, "")
