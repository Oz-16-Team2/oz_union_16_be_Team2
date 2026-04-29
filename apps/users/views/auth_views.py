from django.conf import settings
from django.contrib.auth import logout
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import parsers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from apps.users.serializers.auth_serializers import LoginSerializer
from apps.users.serializers.common_serializers import (
    ErrorDetailFieldListSerializer,
    ErrorDetailStringSerializer,
    ErrorDetailWithdrawnSerializer,
    MessageResponseSerializer,
    TokenResponseSerializer,
)
from apps.users.services.auth_services import login_user, logout_user, refresh_token


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
            OpenApiExample(
                "이메일 로그인 실패 - 필수값 누락",
                value={
                    "error_detail": {
                        "email": ["이 필드는 필수 항목입니다."],
                        "password": ["이 필드는 필수 항목입니다."],
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "이메일 로그인 실패 - 인증 실패",
                value={"error_detail": "이메일 또는 비밀번호가 올바르지 않습니다."},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "이메일 로그인 실패 - 탈퇴 계정",
                value={
                    "error_detail": {
                        "detail": "탈퇴 신청한 계정입니다.",
                        "expire_at": "YYYY-MM-DD",
                    }
                },
                response_only=True,
                status_codes=["403"],
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
            samesite=getattr(settings, "COOKIE_SAME_SITE", "Lax"),
            path="/",
        )
        return response


@extend_schema(tags=["Accounts"])
class LogoutAPIView(APIView):
    serializer_class = MessageResponseSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="로그아웃 API",
        request=None,
        responses={200: MessageResponseSerializer},
        examples=[
            OpenApiExample(
                "로그아웃 성공",
                value={"detail": "로그아웃 되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        refresh_token_value = request.COOKIES.get("refresh_token")

        if refresh_token_value:
            try:
                logout_user(refresh_token=refresh_token_value)
            except TokenError:
                pass

        logout(request)

        response = Response({"detail": "로그아웃 되었습니다."}, status=status.HTTP_200_OK)
        response.delete_cookie(
            key="refresh_token",
            path="/",
            samesite=getattr(settings, "COOKIE_SAME_SITE", "Lax"),
        )
        response.delete_cookie(
            key="sessionid",
            path="/",
            samesite=getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax"),
        )
        return response


@extend_schema(tags=["Accounts"])
class TokenRefreshAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="JWT 토큰 재발급",
        request=None,
        responses={
            200: TokenResponseSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        refresh_token_value = request.COOKIES.get("refresh_token")

        if not refresh_token_value:
            return Response(
                {"error_detail": "로그인 인증이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            result = refresh_token(refresh_token=refresh_token_value)
        except TokenError:
            response = Response(
                {"error_detail": "로그인 인증이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response.delete_cookie(
                key="refresh_token",
                path="/",
                samesite=getattr(settings, "COOKIE_SAME_SITE", "Lax"),
            )
            return response

        return Response(result, status=status.HTTP_200_OK)
