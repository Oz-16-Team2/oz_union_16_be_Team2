from __future__ import annotations

from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.services.common_services import _build_login_payload, _normalize_email, _validate_login_user


def login_user(*, email: str, password: str) -> dict[str, str]:
    email = _normalize_email(email)
    user = User.objects.filter(email__iexact=email).first()

    if user is None or not user.check_password(password):
        raise AuthenticationFailed("이메일 또는 비밀번호가 올바르지 않습니다.")

    user = _validate_login_user(user)
    return _build_login_payload(user)


def logout_user(*, refresh_token: str) -> dict[str, str]:
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError as exc:
        raise AuthenticationFailed("유효하지 않은 토큰입니다.") from exc

    return {"detail": "로그아웃 되었습니다."}


def refresh_token(*, refresh_token: str) -> dict[str, str]:
    try:
        token = RefreshToken(refresh_token)
        return {"access_token": str(token.access_token)}
    except TokenError as exc:
        raise PermissionDenied({"detail": "로그인 세션이 만료되었습니다."}) from exc


def change_password(
    *,
    user: User,
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
