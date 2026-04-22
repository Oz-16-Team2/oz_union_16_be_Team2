from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.choices import UserStatus


class BlockSuspendedUserMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            auth_result = self.jwt_auth.authenticate(request)
        except Exception:
            auth_result = None

        if auth_result is not None:
            user, _ = auth_result
            if user.is_authenticated and user.status == UserStatus.SUSPENDED:
                return JsonResponse(
                    {"error_detail": "정지된 계정입니다."},
                    status=403,
                )

        return self.get_response(request)
