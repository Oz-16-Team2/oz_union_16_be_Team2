from __future__ import annotations

import random
from datetime import timedelta
from typing import Any, cast

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.core.choices import UserStatus
from apps.core.exceptions import ConflictException
from apps.users.models import User


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
        else:
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

    refresh = RefreshToken.for_user(user)

    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }


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


def kakao_social_login() -> dict[str, str]:
    return {"detail": "카카오 로그인 성공"}


def naver_social_login() -> dict[str, str]:
    return {"detail": "네이버 로그인 성공"}


def google_social_login() -> dict[str, str]:
    return {"detail": "구글 로그인 성공"}


def refresh_user_status(user: User) -> User:
    now = timezone.now()

    if user.status == UserStatus.SUSPENDED:
        if user.status_expires_at and user.status_expires_at < now:
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
