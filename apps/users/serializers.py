from typing import Any

from rest_framework import serializers


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
    password = serializers.CharField(write_only=True, min_length=8)
    nickname = serializers.CharField(max_length=30)
    profile_image_url = serializers.CharField(required=False, allow_blank=True)
    email_token = serializers.CharField(max_length=255)


class EmailVerificationSendSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()


class EmailVerificationVerifySerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=20)


class LoginSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenRefreshSerializer(serializers.Serializer[Any]):
    refresh_token = serializers.CharField()


class NicknameCheckSerializer(serializers.Serializer[Any]):
    nickname = serializers.CharField(max_length=30)


class ChangePasswordSerializer(serializers.Serializer[Any]):
    password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["비밀번호가 일치하지 않습니다."]})
        return attrs
