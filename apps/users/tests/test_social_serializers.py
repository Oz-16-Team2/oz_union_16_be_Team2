from apps.users.serializers.social_serializers import SocialLoginSerializer


def test_social_login_serializer_with_code_only() -> None:
    serializer = SocialLoginSerializer(data={"code": "auth-code"})

    assert serializer.is_valid()
    assert serializer.validated_data["code"] == "auth-code"
    assert serializer.validated_data["state"] == ""


def test_social_login_serializer_with_state() -> None:
    serializer = SocialLoginSerializer(data={"code": "auth-code", "state": "state-value"})

    assert serializer.is_valid()
    assert serializer.validated_data["state"] == "state-value"


def test_social_login_serializer_requires_code() -> None:
    serializer = SocialLoginSerializer(data={})

    assert not serializer.is_valid()
    assert "code" in serializer.errors
