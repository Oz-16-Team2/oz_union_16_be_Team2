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
from apps.users.services.social_services import google_social_login, kakao_social_login, naver_social_login


def _get_redirect_uri(request: Request) -> str:
    redirect_uri = request.GET.get("redirect_uri")

    if not redirect_uri:
        raise ValidationError({"redirect_uri": ["이 필드는 필수 항목입니다."]})

    allowed_redirect_uris = getattr(settings, "OAUTH_ALLOWED_REDIRECT_URIS", [])

    if redirect_uri not in allowed_redirect_uris:
        raise ValidationError({"redirect_uri": ["허용되지 않은 redirect_uri입니다."]})

    return redirect_uri


def _social_callback_login(request: Request, *, provider: str) -> Response | HttpResponseRedirect:
    code = request.GET.get("code")
    state = request.GET.get("state", "")

    if code is None:
        raise ValidationError({"code": ["이 필드는 필수 항목입니다."]})

    redirect_uri = _get_redirect_uri(request)

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


SOCIAL_LOGIN_PARAMETERS = [
    OpenApiParameter(name="code", required=True, type=str, location=OpenApiParameter.QUERY),
    OpenApiParameter(name="redirect_uri", required=True, type=str, location=OpenApiParameter.QUERY),
    OpenApiParameter(name="state", required=False, type=str, location=OpenApiParameter.QUERY),
]


@extend_schema(tags=["Accounts"])
class KakaoSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="소셜 카카오 로그인 콜백",
        parameters=SOCIAL_LOGIN_PARAMETERS,
        request=None,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
            409: ErrorDetailFieldListSerializer,
        },
    )
    def get(self, request: Request) -> Response | HttpResponseRedirect:
        return _social_callback_login(request, provider="kakao")


@extend_schema(tags=["Accounts"])
class NaverSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="소셜 네이버 로그인 콜백",
        parameters=SOCIAL_LOGIN_PARAMETERS,
        request=None,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
            409: ErrorDetailFieldListSerializer,
        },
    )
    def get(self, request: Request) -> Response | HttpResponseRedirect:
        return _social_callback_login(request, provider="naver")


@extend_schema(tags=["Accounts"])
class GoogleSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="소셜 구글 로그인 콜백",
        parameters=SOCIAL_LOGIN_PARAMETERS,
        request=None,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
            409: ErrorDetailFieldListSerializer,
        },
    )
    def get(self, request: Request) -> Response | HttpResponseRedirect:
        return _social_callback_login(request, provider="google")
