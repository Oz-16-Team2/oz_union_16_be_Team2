from __future__ import annotations

import json
import secrets
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache  # noqa: F401  # keep parity if you later move helpers here
from rest_framework.exceptions import ValidationError

from apps.core.choices import ProfileImageCode
from apps.users.models import SocialLogin, User
from apps.users.services.common_services import _build_login_payload, _validate_login_user


def _http_json(
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_headers = headers.copy() if headers else {}
    body: bytes | None = None

    if data is not None:
        body = urlencode(data).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")

    req = Request(url=url, data=body, headers=request_headers, method=method)

    try:
        with urlopen(req, timeout=10) as response:
            return cast(dict[str, Any], json.loads(response.read().decode("utf-8")))
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        raise ValidationError({"detail": f"소셜 로그인 요청에 실패했습니다. ({exc.code})", "raw": raw}) from exc
    except URLError as exc:
        raise ValidationError({"detail": "소셜 로그인 서버와 통신할 수 없습니다."}) from exc


def _get_or_create_social_user(
    *,
    provider: str,
    provider_user_id: str,
    email: str,
    nickname: str,
    social_profile_image_url: str | None = None,
) -> User:
    social_login = (
        SocialLogin.objects.select_related("user")
        .filter(
            provider=provider,
            provider_user_id=provider_user_id,
        )
        .first()
    )

    if social_login is not None:
        return _validate_login_user(social_login.user)

    user = User.objects.filter(email__iexact=email).first()

    if user is None:
        user = _create_social_user(
            email=email,
            nickname=nickname,
            social_profile_image_url=social_profile_image_url,
        )
    else:
        user = _validate_login_user(user)

    SocialLogin.objects.create(
        user=user,
        provider=provider,
        provider_user_id=provider_user_id,
    )

    return user


def _get_or_create_unique_nickname(base_nickname: str) -> str:
    nickname = (base_nickname or "user").strip()[:20] or "user"

    if not User.objects.filter(nickname=nickname).exists():
        return nickname

    for _ in range(100):
        candidate = f"{nickname}_{uuid4().hex[:6]}"[:30]
        if not User.objects.filter(nickname=candidate).exists():
            return candidate

    return f"{nickname}_{uuid4().hex[:10]}"[:30]


def _normalize_social_email(provider: str, provider_user_id: str, email: str | None) -> str:
    if email:
        return email.strip().lower()
    return f"{provider}_{provider_user_id}@social.local"


def _create_social_user(
    *,
    email: str,
    nickname: str,
    social_profile_image_url: str | None = None,
) -> User:
    user = User.objects.create_user(
        email=email,
        password=secrets.token_urlsafe(32),
        nickname=_get_or_create_unique_nickname(nickname),
        social_profile_image_url=social_profile_image_url,
        profile_image=ProfileImageCode.AVATAR_01,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    return user


def google_social_login(*, code: str, redirect_uri: str) -> dict[str, str]:
    token_data = _http_json(
        method="POST",
        url="https://oauth2.googleapis.com/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": getattr(settings, "GOOGLE_CLIENT_ID", ""),
            "client_secret": getattr(settings, "GOOGLE_CLIENT_SECRET", ""),
            "redirect_uri": redirect_uri,
        },
    )

    access_token = token_data.get("access_token")
    if not access_token:
        raise ValidationError({"detail": "구글 액세스 토큰을 받을 수 없습니다."})

    profile = _http_json(
        method="GET",
        url="https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    provider_user_id = str(profile.get("sub", ""))
    email = _normalize_social_email("google", provider_user_id, profile.get("email"))
    nickname = profile.get("name") or email.split("@")[0]
    social_profile_image_url = profile.get("picture")

    user = _get_or_create_social_user(
        provider="google",
        provider_user_id=provider_user_id,
        email=email,
        nickname=nickname,
        social_profile_image_url=social_profile_image_url,
    )

    return _build_login_payload(user)


def naver_social_login(*, code: str, redirect_uri: str, state: str) -> dict[str, str]:
    if not state:
        raise ValidationError({"state": ["네이버 로그인에는 state가 필요합니다."]})

    token_data = _http_json(
        method="POST",
        url="https://nid.naver.com/oauth2.0/token",
        data={
            "grant_type": "authorization_code",
            "client_id": getattr(settings, "NAVER_CLIENT_ID", ""),
            "client_secret": getattr(settings, "NAVER_CLIENT_SECRET", ""),
            "code": code,
            "state": state,
            "redirect_uri": redirect_uri,
        },
    )

    access_token = token_data.get("access_token")
    if not access_token:
        raise ValidationError({"detail": "네이버 액세스 토큰을 받을 수 없습니다."})

    profile = _http_json(
        method="GET",
        url="https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    response = profile.get("response") or {}
    provider_user_id = str(response.get("id", ""))
    email = _normalize_social_email("naver", provider_user_id, response.get("email"))
    nickname = response.get("nickname") or email.split("@")[0]
    social_profile_image_url = response.get("profile_image")

    user = _get_or_create_social_user(
        provider="naver",
        provider_user_id=provider_user_id,
        email=email,
        nickname=nickname,
        social_profile_image_url=social_profile_image_url,
    )

    return _build_login_payload(user)


def kakao_social_login(*, code: str, redirect_uri: str) -> dict[str, str]:
    token_payload: dict[str, Any] = {
        "grant_type": "authorization_code",
        "client_id": getattr(settings, "KAKAO_REST_API_KEY", ""),
        "redirect_uri": redirect_uri,
        "code": code,
    }
    client_secret = getattr(settings, "KAKAO_CLIENT_SECRET", "")
    if client_secret:
        token_payload["client_secret"] = client_secret

    token_data = _http_json(
        method="POST",
        url="https://kauth.kakao.com/oauth/token",
        data=token_payload,
    )

    access_token = token_data.get("access_token")
    if not access_token:
        raise ValidationError({"detail": "카카오 액세스 토큰을 받을 수 없습니다."})

    profile = _http_json(
        method="GET",
        url="https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    kakao_account = profile.get("kakao_account") or {}
    kakao_profile = kakao_account.get("profile") or {}

    provider_user_id = str(profile.get("id", ""))
    email = _normalize_social_email("kakao", provider_user_id, kakao_account.get("email"))
    nickname = kakao_profile.get("nickname") or email.split("@")[0]
    social_profile_image_url = kakao_profile.get("profile_image_url")

    user = _get_or_create_social_user(
        provider="kakao",
        provider_user_id=provider_user_id,
        email=email,
        nickname=nickname,
        social_profile_image_url=social_profile_image_url,
    )

    return _build_login_payload(user)
