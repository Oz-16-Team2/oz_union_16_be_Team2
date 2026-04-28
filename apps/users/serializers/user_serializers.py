import re
from typing import Any

from rest_framework import serializers

from apps.core.choices import ProfileImageCode
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User

PROFILE_IMAGE_CODE_BY_URL = {url: code for code, url in PROFILE_IMAGE_URL_MAP.items()}


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
    profile_image_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    profile_image = serializers.ChoiceField(
        choices=ProfileImageCode.choices,
        required=False,
        default=ProfileImageCode.AVATAR_01,
    )
    email_token = serializers.CharField(required=True, max_length=1024)

    def validate_password(self, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise serializers.ValidationError("비밀번호 형식이 올바르지 않습니다.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        profile_image_url = (attrs.pop("profile_image_url", "") or "").strip()
        profile_image = attrs.pop("profile_image", ProfileImageCode.AVATAR_01)

        if profile_image_url:
            mapped_profile_image = PROFILE_IMAGE_CODE_BY_URL.get(profile_image_url)
            if mapped_profile_image is None:
                raise serializers.ValidationError({"profile_image_url": ["지원하지 않는 프로필 이미지입니다."]})
            attrs["profile_image"] = mapped_profile_image
        else:
            attrs["profile_image"] = profile_image

        return attrs


class EmailVerificationSendSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()


class EmailVerificationVerifySerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=20)


class LoginSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class SocialLoginSerializer(serializers.Serializer[Any]):
    code = serializers.CharField()
    redirect_uri = serializers.URLField()
    state = serializers.CharField(required=False, allow_blank=True, default="")


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

    def validate_new_password(self, value: str) -> str:
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise serializers.ValidationError("비밀번호 형식이 올바르지 않습니다.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": ["비밀번호가 일치하지 않습니다."]})
        return attrs


class UserProfileSerializer(serializers.ModelSerializer[Any]):
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "nickname", "profile_image_url"]

    def get_profile_image_url(self, obj: User) -> str:
        return PROFILE_IMAGE_URL_MAP.get(obj.profile_image, "")


class MeActivitySummaryDaysDetailSerializer(serializers.Serializer[Any]):
    days_together = serializers.IntegerField()


class MeActivitySummaryDaysResponseSerializer(serializers.Serializer[Any]):
    detail = MeActivitySummaryDaysDetailSerializer()


class MeActivitySummaryAchievementRateDetailSerializer(serializers.Serializer[Any]):
    total_goals_count = serializers.IntegerField()
    completed_goals_count = serializers.IntegerField()
    total_achievement_rate = serializers.FloatField()


class MeActivitySummaryAchievementRateResponseSerializer(serializers.Serializer[Any]):
    detail = MeActivitySummaryAchievementRateDetailSerializer()


class MeActivitySummaryCompletedGoalsDetailSerializer(serializers.Serializer[Any]):
    completed_goals_count = serializers.IntegerField()


class MeActivitySummaryCompletedGoalsResponseSerializer(serializers.Serializer[Any]):
    detail = MeActivitySummaryCompletedGoalsDetailSerializer()
