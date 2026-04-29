from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from drf_spectacular.utils import OpenApiParameter, extend_schema
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


def _oauth_callback_url(provider: str) -> str:
    base = getattr(settings, "BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{base}/api/v1/accounts/social-login/{provider}/callback"


def _social_callback_login(request: Request, *, provider: str) -> Response | HttpResponseRedirect:
    code = request.GET.get("code")
    state = request.GET.get("state", "")

    if code is None:
        raise ValidationError({"code": ["이 필드는 필수 항목입니다."]})

    redirect_uri = _oauth_callback_url(provider)

    if provider == "google":
        result = google_social_login(code=code, redirect_uri=redirect_uri)
    elif provider == "naver":
        if not state:
            raise ValidationError({"state": ["이 필드는 필수 항목입니다."]})
        result = naver_social_login(code=code, redirect_uri=redirect_uri, state=state)
    elif provider == "kakao":
        result = kakao_social_login(code=code, redirect_uri=redirect_uri)
    else:
        raise ValidationError({"detail": ["지원하지 않는 provider 입니다."]})

    refresh_token_value = result["refresh_token"]

    frontend_url = getattr(
        settings,
        "FRONTEND_BASE_URL",
        "https://oz-union-16-fe-team2.vercel.app",
    )
    response = redirect(frontend_url)

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
class KakaoSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="소셜 카카오 로그인 콜백",
        parameters=[OpenApiParameter(name="code", required=True, type=str)],
        request=None,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
        },
    )
    def get(self, request: Request) -> Response | HttpResponseRedirect:
        serializer = SocialLoginSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return _social_callback_login(request, provider="kakao")


@extend_schema(tags=["Accounts"])
class NaverSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="소셜 네이버 로그인 콜백",
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
    )
    def get(self, request: Request) -> Response | HttpResponseRedirect:
        serializer = SocialLoginSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return _social_callback_login(request, provider="naver")


@extend_schema(tags=["Accounts"])
class GoogleSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="소셜 구글 로그인 콜백",
        parameters=[OpenApiParameter(name="code", required=True, type=str)],
        request=None,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
        },
    )
    def get(self, request: Request) -> Response | HttpResponseRedirect:
        serializer = SocialLoginSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return _social_callback_login(request, provider="google")
