from typing import Any

from rest_framework import serializers

from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import SocialLogin, User


class UserProfileSerializer(serializers.ModelSerializer[Any]):
    nickname = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "nickname", "profile_image_url"]

    def _get_social_login(self, obj: User) -> SocialLogin | None:
        request = self.context.get("request")
        if request is None or request.auth is None:
            return None

        provider = request.auth.get("provider")
        if not isinstance(provider, str) or not provider:
            return None

        return obj.social_logins.filter(provider=provider).first()

    def get_nickname(self, obj: User) -> str:
        social_login = self._get_social_login(obj)

        if social_login is not None and social_login.social_nickname:
            return str(social_login.social_nickname)

        return str(obj.nickname)

    def get_profile_image_url(self, obj: User) -> str:
        social_login = self._get_social_login(obj)

        if social_login is not None and social_login.social_profile_image_url:
            return str(social_login.social_profile_image_url)

        return str(PROFILE_IMAGE_URL_MAP.get(obj.profile_image, ""))


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


class ProfileImageSerializer(serializers.Serializer[Any]):
    code = serializers.CharField()
    image_url = serializers.CharField()


class ProfileImageListResponseSerializer(serializers.Serializer[Any]):
    detail = ProfileImageSerializer(many=True)
