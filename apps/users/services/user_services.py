from __future__ import annotations

import json
import random
import secrets
from datetime import timedelta
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.core.choices import ProfileImageCode, UserStatus
from apps.core.exceptions import ConflictException
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User


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


def _get_or_create_unique_nickname(base_nickname: str) -> str:
    nickname = (base_nickname or "user")[:30]
    if not User.objects.filter(nickname=nickname).exists():
        return nickname

    for _ in range(100):
        suffix = secrets.token_hex(2)
        candidate = f"{nickname[:25]}_{suffix}"[:30]
        if not User.objects.filter(nickname=candidate).exists():
            return candidate

    return f"{nickname[:20]}_{secrets.token_hex(4)}"[:30]


def _build_user_profile(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "nickname": user.nickname,
        "profile_image_url": PROFILE_IMAGE_URL_MAP.get(user.profile_image, ""),
    }


def _build_login_payload(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }


def _validate_login_user(user: User) -> User:
    user = refresh_user_status(user)

    deleted_at = getattr(user, "deleted_at", None)
    if deleted_at is not None:
        raise PermissionDenied(
            {
                "detail": "탈퇴 신청한 계정입니다.",
                "expire_at": deleted_at.strftime("%Y-%m-%d"),
            }
        )
    if user.status == UserStatus.SUSPENDED:
        raise PermissionDenied("정지된 계정입니다.")

    return user


def _normalize_social_email(provider: str, provider_user_id: str, email: str | None) -> str:
    if email:
        return email.strip().lower()
    return f"{provider}_{provider_user_id}@social.local"


def _create_social_user(*, email: str, nickname: str) -> User:
    return User.objects.create_user(
        email=email,
        password=secrets.token_urlsafe(32),
        nickname=_get_or_create_unique_nickname(nickname),
        profile_image=ProfileImageCode.AVATAR_01,
    )


def signup_user(
    *,
    email: str,
    password: str,
    nickname: str,
    profile_image: str,
    email_token: str,
) -> dict[str, str]:
    if not email_token:
        raise ValidationError({"email_token": ["이메일 인증이 필요합니다."]})

    try:
        token_email = verify_email_token(email_token)
    except ValueError as e:
        if str(e) == "expired":
            raise ValidationError({"email_token": ["이메일 토큰이 만료되었습니다. 다시 인증해주세요."]}) from e
        raise ValidationError({"email_token": ["유효하지 않은 이메일 토큰입니다."]}) from e

    if token_email != email:
        raise ValidationError({"email_token": ["이메일 정보가 일치하지 않습니다."]})

    if is_token_used(email_token):
        raise ValidationError({"email_token": ["이미 사용된 이메일 토큰입니다."]})

    errors: dict[str, list[str]] = {}

    if User.objects.filter(email=email).exists():
        errors["email"] = ["이미 가입된 이메일입니다."]

    if User.objects.filter(nickname=nickname).exists():
        errors["nickname"] = ["이미 사용 중인 닉네임입니다."]

    if errors:
        raise ConflictException(errors)

    User.objects.create_user(
        email=email,
        password=password,
        nickname=nickname,
        profile_image=profile_image,
    )

    mark_token_used(email_token)
    return {"detail": "회원가입이 완료되었습니다."}


def check_nickname(*, nickname: str) -> dict[str, str]:
    if User.objects.filter(nickname=nickname).exists():
        raise ConflictException({"nickname": ["이미 사용 중인 닉네임입니다."]})
    return {"detail": "사용가능한 닉네임입니다."}


def login_user(*, email: str, password: str) -> dict[str, str]:
    user = User.objects.filter(email=email).first()

    if user is None or not user.check_password(password):
        raise AuthenticationFailed("이메일 또는 비밀번호가 올바르지 않습니다.")

    user = _validate_login_user(user)
    return _build_login_payload(user)


def logout_user(*, refresh_token: str) -> dict[str, str]:
    try:
        token = RefreshToken(cast(Any, refresh_token))
        token.blacklist()
    except TokenError as exc:
        raise AuthenticationFailed("유효하지 않은 토큰입니다.") from exc

    return {"detail": "로그아웃 되었습니다."}


def refresh_token(*, refresh_token: str) -> dict[str, str]:
    try:
        token = RefreshToken(cast(Any, refresh_token))
        return {"access_token": str(token.access_token)}
    except TokenError as exc:
        raise PermissionDenied({"detail": "로그인 세션이 만료되었습니다."}) from exc


def change_password(
    *,
    user: Any,
    password: str,
    new_password: str,
) -> dict[str, str]:
    if not user.is_authenticated:
        raise AuthenticationFailed("로그인 인증이 필요합니다.")

    if not user.check_password(password):
        raise PermissionDenied("기존 비밀번호가 일치하지 않습니다.")

    user.set_password(new_password)
    user.save(update_fields=["password"])
    return {"detail": "비밀번호가 변경되었습니다."}


def send_email_verification_code(*, email: str) -> dict[str, str]:
    code = str(random.randint(100000, 999999))

    cache.set(f"email_code:{email}", code, timeout=settings.EMAIL_VERIFICATION_TIMEOUT)

    send_mail(
        subject="이메일 인증 코드",
        message=f"인증 코드: {code}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return {"detail": "이메일 인증 코드가 전송되었습니다."}


def verify_email(*, email: str, code: str) -> dict[str, str]:
    saved_code = cache.get(f"email_code:{email}")

    if saved_code is None:
        raise ValidationError({"code": ["인증 시간이 만료되었습니다."]})

    if saved_code != code:
        raise ValidationError({"code": ["인증 코드가 올바르지 않습니다."]})

    cache.delete(f"email_code:{email}")
    token = generate_email_token(email)

    return {
        "detail": "이메일 인증에 성공하였습니다.",
        "email_token": token,
    }


def google_social_login(*, code: str, redirect_uri: str, state: str = "") -> dict[str, str]:
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

    user = User.objects.filter(email=email).first()
    if user is None:
        user = _create_social_user(email=email, nickname=nickname)
    else:
        user = _validate_login_user(user)

    return _build_login_payload(user)


def naver_social_login(*, code: str, redirect_uri: str, state: str = "") -> dict[str, str]:
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

    user = User.objects.filter(email=email).first()
    if user is None:
        user = _create_social_user(email=email, nickname=nickname)
    else:
        user = _validate_login_user(user)

    return _build_login_payload(user)


def kakao_social_login(*, code: str, redirect_uri: str, state: str = "") -> dict[str, str]:
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

    user = User.objects.filter(email=email).first()
    if user is None:
        user = _create_social_user(email=email, nickname=nickname)
    else:
        user = _validate_login_user(user)

    return _build_login_payload(user)


def get_my_profile(user: User) -> dict[str, Any]:
    return _build_user_profile(user)


def refresh_user_status(user: User) -> User:
    now = timezone.now()

    if user.status == UserStatus.SUSPENDED and user.status_expires_at and user.status_expires_at < now:
        user.status = UserStatus.ACTIVE
        user.status_expires_at = None
        user.memo = None
        user.save(update_fields=["status", "status_expires_at", "memo", "updated_at"])

    return user


def generate_email_token(email: str) -> str:
    token = AccessToken()
    token["email"] = email
    token["type"] = "email_verification"
    token.set_exp(lifetime=timedelta(minutes=10))
    return str(token)


def verify_email_token(token: str) -> str:
    try:
        decoded = AccessToken(cast(Any, token))

        if decoded.get("type") != "email_verification":
            raise ValueError("invalid type")

        return str(decoded["email"])

    except TokenError as err:
        raise ValueError("expired") from err

    except Exception as err:
        raise ValueError("invalid") from err


def is_token_used(token: str) -> bool:
    return cache.get(f"used_email_token:{token}") is not None


def mark_token_used(token: str) -> None:
    cache.set(f"used_email_token:{token}", True, timeout=900)
