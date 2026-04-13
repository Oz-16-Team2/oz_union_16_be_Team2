from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminRole(permissions.BasePermission):
    message = "권한이 없습니다."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
