from django.contrib.auth import get_user_model

from apps.core.exceptions import ConflictException

User = get_user_model()


def signup_user(*, email: str, password: str, nickname: str) -> dict[str, str]:
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
    )

    return {"detail": "회원가입이 완료되었습니다."}


def check_nickname(*, nickname: str) -> dict[str, str]:
    if User.objects.filter(nickname=nickname).exists():
        raise ConflictException({"nickname": ["이미 사용 중인 닉네임입니다."]})

    return {"detail": "사용가능한 닉네임입니다."}


# ======================
# stub 함수들 (타입 추가)
# ======================


def change_password() -> dict[str, str]:
    return {"detail": "비밀번호가 변경되었습니다."}


def login_user() -> dict[str, str]:
    return {"detail": "로그인이 되었습니다."}


def logout_user() -> dict[str, str]:
    return {"detail": "로그아웃 되었습니다."}


def refresh_token() -> dict[str, str]:
    return {"detail": "토큰이 재발급되었습니다."}


def send_email_verification_code() -> dict[str, str]:
    return {"detail": "이메일 인증 코드가 전송되었습니다."}


def verify_email() -> dict[str, str]:
    return {"detail": "이메일 인증에 성공하였습니다."}


def kakao_social_login() -> dict[str, str]:
    return {"detail": "카카오 로그인 성공"}


def naver_social_login() -> dict[str, str]:
    return {"detail": "네이버 로그인 성공"}


def google_social_login() -> dict[str, str]:
    return {"detail": "구글 로그인 성공"}
