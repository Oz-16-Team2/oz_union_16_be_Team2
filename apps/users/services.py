def signup_user() -> dict[str, str]:
    return {
        "detail": "회원가입이 완료되었습니다.",
    }


def send_email_verification_code() -> dict[str, str]:
    return {
        "detail": "이메일 인증 코드가 전송되었습니다.",
    }


def verify_email() -> dict[str, str]:
    return {
        "detail": "이메일 인증에 성공하였습니다.",
        "email_token": "daechungbase32",
    }


def kakao_social_login() -> dict[str, str]:
    return {
        "access_token": "JWT Token Value",
    }


def naver_social_login() -> dict[str, str]:
    return {
        "access_token": "JWT Token Value",
    }


def google_social_login() -> dict[str, str]:
    return {
        "access_token": "JWT Token Value",
    }


def login_user() -> dict[str, str]:
    return {
        "access_token": "JWT Token Value",
    }


def logout_user() -> dict[str, str]:
    return {
        "detail": "로그아웃 되었습니다.",
    }


def refresh_token() -> dict[str, str]:
    return {
        "access_token": "JWT Token Value",
    }


def check_nickname() -> dict[str, str]:
    return {
        "detail": "사용가능한 닉네임입니다.",
    }


def change_password() -> dict[str, str]:
    return {
        "detail": "비밀번호가 변경되었습니다.",
    }
