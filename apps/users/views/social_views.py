from django.conf import settings
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.common_serializers import (
    ErrorDetailFieldListSerializer,
    ErrorDetailStringSerializer,
    TokenResponseSerializer,
)
from apps.users.serializers.social_serializers import SocialLoginSerializer
from apps.users.services.social_services import google_social_login, kakao_social_login, naver_social_login


def _social_login_response(result: dict[str, str]) -> Response:
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


class SocialLoginCallbackMixin:
    serializer_class = SocialLoginSerializer
    permission_classes = [AllowAny]
    provider: str = ""

    def _login(self, request: Request, *, code: str, state: str = "") -> Response:
        redirect_uri = request.build_absolute_uri(request.path)

        if self.provider == "google":
            result = google_social_login(code=code, redirect_uri=redirect_uri)
        elif self.provider == "naver":
            if not state:
                raise ValidationError({"state": ["이 필드는 필수 항목입니다."]})
            result = naver_social_login(code=code, redirect_uri=redirect_uri, state=state)
        elif self.provider == "kakao":
            result = kakao_social_login(code=code, redirect_uri=redirect_uri)
        else:
            raise ValidationError({"detail": ["지원하지 않는 provider 입니다."]})

        return _social_login_response(result)


@extend_schema(tags=["Accounts"])
class GoogleSocialLoginAPIView(SocialLoginCallbackMixin, APIView):
    provider = "google"

    @extend_schema(
        summary="소셜 구글 로그인",
        parameters=[OpenApiParameter(name="code", required=True, type=str)],
        request=None,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "소셜 로그인 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return self._login(
            request,
            code=serializer.validated_data["code"],
            state="",
        )


@extend_schema(tags=["Accounts"])
class NaverSocialLoginAPIView(SocialLoginCallbackMixin, APIView):
    provider = "naver"

    @extend_schema(
        summary="소셜 네이버 로그인",
        parameters=[
            OpenApiParameter(name="code", required=True, type=str),
            OpenApiParameter(name="state", required=True, type=str),
        ],
        request=None,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "소셜 로그인 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return self._login(
            request,
            code=serializer.validated_data["code"],
            state=serializer.validated_data["state"],
        )


@extend_schema(tags=["Accounts"])
class KakaoSocialLoginAPIView(SocialLoginCallbackMixin, APIView):
    provider = "kakao"

    @extend_schema(
        summary="소셜 카카오 로그인",
        parameters=[OpenApiParameter(name="code", required=True, type=str)],
        request=None,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "소셜 로그인 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return self._login(
            request,
            code=serializer.validated_data["code"],
            state="",
        )
