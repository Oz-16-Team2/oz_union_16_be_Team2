# apps/core/permissions.py

from rest_framework.permissions import BasePermission
from apps.core.choices import UserStatus


class CanWriteGoal(BasePermission):
    message = "정지된 계정은 목표를 생성할 수 없습니다."

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.status != UserStatus.SUSPENDED


class CanWriteCommunity(BasePermission):
    message = "제한된 계정은 커뮤니티 기능을 사용할 수 없습니다."

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.status == UserStatus.SUSPENDED:
            self.message = "정지된 계정은 해당 기능을 사용할 수 없습니다."
            return False

        if user.status == UserStatus.RESTRICTED:
            return False

        return True


class CanUseInteraction(BasePermission):
    message = "정지된 계정은 해당 기능을 사용할 수 없습니다."

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.status != UserStatus.SUSPENDED