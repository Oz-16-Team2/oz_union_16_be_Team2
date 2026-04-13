from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

ADMIN_ROLES = {"ADMIN", "TA", "OM", "LC"}


class IsAdminRole(permissions.BasePermission):  # type: ignore[misc]
    message = "권한이 없습니다."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user and request.user.is_authenticated and getattr(request.user, "role", None) in ADMIN_ROLES
        )
