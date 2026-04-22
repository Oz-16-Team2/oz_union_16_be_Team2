from collections.abc import Callable
from typing import cast

from django.http import HttpRequest, HttpResponse
from rest_framework.exceptions import PermissionDenied

from apps.core.choices import UserStatus
from apps.users.models import User


class BlockSuspendedUserMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = cast(User, request.user)

        if user.is_authenticated and user.status == UserStatus.SUSPENDED:
            raise PermissionDenied("정지된 계정입니다.")

        return self.get_response(request)
