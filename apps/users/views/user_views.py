from typing import Any, Literal, cast
from urllib.parse import urlencode

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import parsers, status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ConflictException
from apps.users.serializers.user_serializers import (
    ChangePasswordSerializer,
    EmailVerificationSendSerializer,
    EmailVerificationSuccessSerializer,
    EmailVerificationVerifySerializer,
    ErrorDetailFieldListSerializer,
    ErrorDetailStringSerializer,
    ErrorDetailWithdrawnSerializer,
    LoginSerializer,
    MeActivitySummaryAchievementRateResponseSerializer,
    MeActivitySummaryCompletedGoalsResponseSerializer,
    MeActivitySummaryDaysResponseSerializer,
    MessageResponseSerializer,
    NaverSocialLoginSerializer,
    NicknameCheckSerializer,
    SignupSerializer,
    SocialLoginSerializer,
    TokenRefreshSerializer,
    TokenResponseSerializer,
    UserProfileSerializer,
)
from apps.users.services.user_services import (
    change_password,
    check_nickname,
    get_me_activity_summary_achievement_rate,
    get_me_activity_summary_completed_goals,
    get_me_activity_summary_days,
    get_my_profile,
    google_social_login,
    kakao_social_login,
    login_user,
    logout_user,
    naver_social_login,
    refresh_token,
    send_email_verification_code,
    signup_user,
    verify_email,
)

NAVER_TEST_STATE = "swagger-test-state"


def _backend_base_url() -> str:
    return getattr(settings, "BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _oauth_callback_url(provider: str) -> str:
    return f"{_backend_base_url()}/api/v1/accounts/social-login/{provider}/callback/"


def _google_auth_url() -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": getattr(settings, "GOOGLE_CLIENT_ID", ""),
            "redirect_uri": _oauth_callback_url("google"),
            "scope": "openid email profile",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def _naver_auth_url() -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": getattr(settings, "NAVER_CLIENT_ID", ""),
            "redirect_uri": _oauth_callback_url("naver"),
            "state": NAVER_TEST_STATE,
        }
    )
    return f"https://nid.naver.com/oauth2.0/authorize?{query}"


def _kakao_auth_url() -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": getattr(settings, "KAKAO_REST_API_KEY", ""),
            "redirect_uri": _oauth_callback_url("kakao"),
        }
    )
    return f"https://kauth.kakao.com/oauth/authorize?{query}"


def _social_login_response(result: dict[str, str]) -> Response:
    refresh_token_value = result.pop("refresh_token")

    response = Response(result, status=status.HTTP_200_OK)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,
        samesite="Lax",
    )
    return response


def _social_callback_response(request: Request) -> Response:
    code = request.GET.get("code")
    state = request.GET.get("state", "")

    if code is None:
        raise ValidationError({"code": ["이 필드는 필수 항목입니다."]})

    return Response(
        {"code": code, "state": state},
        status=status.HTTP_200_OK,
    )


@extend_schema(tags=["Accounts"])
class SignupAPIView(APIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="이메일 회원가입",
        request=SignupSerializer,
        responses={
            201: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            409: ErrorDetailFieldListSerializer,
        },
        examples=[
            OpenApiExample(
                "회원가입 성공",
                value={"detail": "회원가입이 완료되었습니다."},
                response_only=True,
                status_codes=["201"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = signup_user(**serializer.validated_data)
        except ConflictException as exc:
            return Response({"error_detail": exc.detail}, status=status.HTTP_409_CONFLICT)

        return Response(result, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Accounts"])
class NicknameCheckAPIView(APIView):
    serializer_class = NicknameCheckSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="닉네임 중복 확인 API",
        parameters=[OpenApiParameter(name="nickname", required=True, type=str)],
        responses={
            200: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            409: ErrorDetailFieldListSerializer,
        },
        examples=[
            OpenApiExample(
                "닉네임 사용 가능",
                value={"detail": "사용가능한 닉네임입니다."},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            result = check_nickname(**serializer.validated_data)
        except ConflictException as exc:
            return Response({"error_detail": exc.detail}, status=status.HTTP_409_CONFLICT)

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class EmailVerificationSendAPIView(APIView):
    serializer_class = EmailVerificationSendSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="이메일 인증 발송 API",
        request=EmailVerificationSendSerializer,
        responses={
            200: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            409: ErrorDetailFieldListSerializer,
        },
        examples=[
            OpenApiExample(
                "인증 메일 발송 성공",
                value={"detail": "이메일 인증 코드가 전송되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = send_email_verification_code(**serializer.validated_data)
        except ConflictException as exc:
            return Response({"error_detail": exc.detail}, status=status.HTTP_409_CONFLICT)

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class EmailVerificationVerifyAPIView(APIView):
    serializer_class = EmailVerificationVerifySerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="이메일 인증 확인",
        request=EmailVerificationVerifySerializer,
        responses={
            200: EmailVerificationSuccessSerializer,
            400: ErrorDetailFieldListSerializer,
        },
        examples=[
            OpenApiExample(
                "이메일 인증 성공",
                value={
                    "detail": "이메일 인증에 성공하였습니다.",
                    "email_token": "daechungbase32",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = verify_email(
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
        )
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class KakaoSocialLoginAPIView(APIView):
    serializer_class = SocialLoginSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="소셜 카카오 로그인 callback",
        description=f"**[카카오 로그인 버튼 (클릭)]({_kakao_auth_url()})**",
        parameters=[
            OpenApiParameter(name="code", required=False, type=str),
            OpenApiParameter(name="state", required=False, type=str),
        ],
        responses={200: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                "callback 코드 확인",
                value={"code": "4/0AeoWuM-...", "state": ""},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        return _social_callback_response(request)

    @extend_schema(
        summary="소셜 카카오 회원가입,로그인",
        description=f"**[카카오 로그인 버튼 (클릭)]({_kakao_auth_url()})**",
        request=SocialLoginSerializer,
        responses={200: TokenResponseSerializer},
        examples=[
            OpenApiExample(
                "소셜 로그인 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = kakao_social_login(**serializer.validated_data)
        return _social_login_response(result)


@extend_schema(tags=["Accounts"])
class NaverSocialLoginAPIView(APIView):
    serializer_class = NaverSocialLoginSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="소셜 네이버 로그인 callback",
        description=f"**[네이버 로그인 버튼 (클릭)]({_naver_auth_url()})**",
        parameters=[
            OpenApiParameter(name="code", required=False, type=str),
            OpenApiParameter(name="state", required=False, type=str),
        ],
        responses={200: TokenResponseSerializer},
        examples=[
            OpenApiExample(
                "callback 코드 확인",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        return _social_callback_response(request)

    @extend_schema(
        summary="소셜 네이버 회원가입,로그인",
        description=f"**[네이버 로그인 버튼 (클릭)]({_naver_auth_url()})**",
        request=NaverSocialLoginSerializer,
        responses={200: TokenResponseSerializer},
        examples=[
            OpenApiExample(
                "소셜 로그인 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = naver_social_login(**serializer.validated_data)
        return _social_login_response(result)


@extend_schema(tags=["Accounts"])
class GoogleSocialLoginAPIView(APIView):
    serializer_class = SocialLoginSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="소셜 구글 로그인 callback",
        description=f"**[구글 로그인 버튼 (클릭)]({_google_auth_url()})**",
        parameters=[
            OpenApiParameter(name="code", required=False, type=str),
            OpenApiParameter(name="state", required=False, type=str),
        ],
        responses={200: TokenResponseSerializer},
        examples=[
            OpenApiExample(
                "callback 코드 확인",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        return _social_callback_response(request)

    @extend_schema(
        summary="소셜 구글 회원가입,로그인",
        description=f"**[구글 로그인 버튼 (클릭)]({_google_auth_url()})**",
        request=SocialLoginSerializer,
        responses={200: TokenResponseSerializer},
        examples=[
            OpenApiExample(
                "소셜 로그인 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = google_social_login(**serializer.validated_data)
        return _social_login_response(result)


@extend_schema(tags=["Accounts"])
class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="이메일 로그인",
        request=LoginSerializer,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailWithdrawnSerializer,
        },
        examples=[
            OpenApiExample(
                "이메일 로그인 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = login_user(**serializer.validated_data)
        refresh_token_value = result.pop("refresh_token")

        response = Response(result, status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token_value,
            httponly=True,
            secure=getattr(settings, "COOKIE_SECURE", False),
            samesite=cast(Literal["Lax", "Strict", "None", False], getattr(settings, "COOKIE_SAME_SITE", "Lax")),
            path="/",
        )
        return response


@extend_schema(tags=["Accounts"])
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 프로필 조회",
        responses={200: UserProfileSerializer},
        examples=[
            OpenApiExample(
                "내 프로필 조회 성공",
                value={
                    "id": 1,
                    "nickname": "testnick",
                    "profile_image_url": "https://example.com/profile.png",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        return Response(get_my_profile(request.user), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class MeActivitySummaryDaysAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="함께한 기간",
        responses={200: MeActivitySummaryDaysResponseSerializer, 401: ErrorDetailStringSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(get_me_activity_summary_days(request.user), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class MeActivitySummaryAchievementRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="전체 달성률",
        responses={200: MeActivitySummaryAchievementRateResponseSerializer, 401: ErrorDetailStringSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(get_me_activity_summary_achievement_rate(request.user), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class MeActivitySummaryCompletedGoalsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="완료한 일정",
        responses={200: MeActivitySummaryCompletedGoalsResponseSerializer, 401: ErrorDetailStringSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(get_me_activity_summary_completed_goals(request.user), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class LogoutAPIView(APIView):
    serializer_class = MessageResponseSerializer
    permission_classes = [AllowAny]

    @extend_schema(summary="로그아웃 API", request=None, responses={200: MessageResponseSerializer})
    def post(self, request: Request) -> Response:
        refresh_token_value = request.COOKIES.get("refresh_token")

        if refresh_token_value:
            logout_user(refresh_token=refresh_token_value)

        response = Response({"detail": "로그아웃 되었습니다."}, status=status.HTTP_200_OK)
        samesite = cast(Literal["Lax", "Strict", "None", False], getattr(settings, "COOKIE_SAME_SITE", "Lax"))
        response.delete_cookie(
            "refresh_token",
            path="/",
            samesite=samesite,
        )
        return response


@extend_schema(tags=["Accounts"])
class TokenRefreshAPIView(APIView):
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="JWT 토큰 재발급",
        request=TokenRefreshSerializer,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "토큰 재발급 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = refresh_token(**serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class ChangePasswordAPIView(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="비밀번호 변경",
        request=ChangePasswordSerializer,
        responses={
            200: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
        },
    )
    def patch(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = change_password(
            user=request.user,
            password=serializer.validated_data["password"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response(result, status=status.HTTP_200_OK)
