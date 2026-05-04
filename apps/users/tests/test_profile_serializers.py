import pytest

from apps.core.choices import ProfileImageCode
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import SocialLogin, User
from apps.users.serializers.profile_serializers import (
    ChangeNicknameSerializer,
    MeActivitySummaryAchievementRateResponseSerializer,
    MeActivitySummaryCompletedGoalsResponseSerializer,
    MeActivitySummaryDaysResponseSerializer,
    ProfileImageListResponseSerializer,
    UserProfileSerializer,
)


class DummyRequest:
    def __init__(self, auth: dict[str, str] | None = None) -> None:
        self.auth = auth


@pytest.mark.django_db
def test_user_profile_serializer_returns_default_user_profile(user: User) -> None:
    serializer = UserProfileSerializer(user)

    assert serializer.data == {
        "id": user.id,
        "nickname": user.nickname,
        "profile_image_url": PROFILE_IMAGE_URL_MAP.get(user.profile_image, ""),
    }


@pytest.mark.django_db
def test_user_profile_serializer_returns_default_when_request_is_none(user: User) -> None:
    serializer = UserProfileSerializer(user, context={"request": None})

    assert serializer.data["nickname"] == user.nickname
    assert serializer.data["profile_image_url"] == PROFILE_IMAGE_URL_MAP.get(user.profile_image, "")


@pytest.mark.django_db
def test_user_profile_serializer_returns_default_when_auth_is_none(user: User) -> None:
    request = DummyRequest(auth=None)
    serializer = UserProfileSerializer(user, context={"request": request})

    assert serializer.data["nickname"] == user.nickname
    assert serializer.data["profile_image_url"] == PROFILE_IMAGE_URL_MAP.get(user.profile_image, "")


@pytest.mark.django_db
def test_user_profile_serializer_returns_default_when_provider_is_invalid(user: User) -> None:
    request = DummyRequest(auth={"provider": ""})
    serializer = UserProfileSerializer(user, context={"request": request})

    assert serializer.data["nickname"] == user.nickname
    assert serializer.data["profile_image_url"] == PROFILE_IMAGE_URL_MAP.get(user.profile_image, "")


@pytest.mark.django_db
def test_user_profile_serializer_returns_social_profile(user: User) -> None:
    SocialLogin.objects.create(
        user=user,
        provider="kakao",
        provider_user_id="kakao-user-id",
        social_nickname="카카오닉네임",
        social_profile_image_url="https://example.com/kakao-profile.png",
    )
    request = DummyRequest(auth={"provider": "kakao"})

    serializer = UserProfileSerializer(user, context={"request": request})

    assert serializer.data["nickname"] == "카카오닉네임"
    assert serializer.data["profile_image_url"] == "https://example.com/kakao-profile.png"


@pytest.mark.django_db
def test_user_profile_serializer_returns_user_profile_when_social_values_empty(user: User) -> None:
    SocialLogin.objects.create(
        user=user,
        provider="naver",
        provider_user_id="naver-user-id",
        social_nickname="",
        social_profile_image_url="",
    )
    request = DummyRequest(auth={"provider": "naver"})

    serializer = UserProfileSerializer(user, context={"request": request})

    assert serializer.data["nickname"] == user.nickname
    assert serializer.data["profile_image_url"] == PROFILE_IMAGE_URL_MAP.get(user.profile_image, "")


def test_me_activity_summary_days_response_serializer_valid() -> None:
    serializer = MeActivitySummaryDaysResponseSerializer(
        data={
            "detail": {
                "days_together": 10,
            }
        }
    )

    assert serializer.is_valid() is True


def test_me_activity_summary_achievement_rate_response_serializer_valid() -> None:
    serializer = MeActivitySummaryAchievementRateResponseSerializer(
        data={
            "detail": {
                "total_goals_count": 10,
                "completed_goals_count": 7,
                "total_achievement_rate": 70,
            }
        }
    )

    assert serializer.is_valid() is True


def test_me_activity_summary_completed_goals_response_serializer_valid() -> None:
    serializer = MeActivitySummaryCompletedGoalsResponseSerializer(
        data={
            "detail": {
                "completed_goals_count": 7,
            }
        }
    )

    assert serializer.is_valid() is True


def test_profile_image_list_response_serializer_valid() -> None:
    serializer = ProfileImageListResponseSerializer(
        data={
            "detail": [
                {
                    "code": ProfileImageCode.AVATAR_01,
                    "image_url": "https://example.com/avatar.png",
                }
            ]
        }
    )

    assert serializer.is_valid() is True


def test_change_nickname_serializer_valid() -> None:
    serializer = ChangeNicknameSerializer(data={"nickname": "새닉네임"})

    assert serializer.is_valid() is True
    assert serializer.validated_data["nickname"] == "새닉네임"


def test_change_nickname_serializer_required() -> None:
    serializer = ChangeNicknameSerializer(data={})

    assert serializer.is_valid() is False
    assert "nickname" in serializer.errors


def test_change_nickname_serializer_max_length() -> None:
    serializer = ChangeNicknameSerializer(data={"nickname": "a" * 31})

    assert serializer.is_valid() is False
    assert "nickname" in serializer.errors
