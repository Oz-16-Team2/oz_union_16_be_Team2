# apps/users/views/admin/admin_user_views.py

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.admin.base_views import AdminBaseAPIView
from apps.core.common_serializers import DetailMessageSerializer, ErrorDetailStringSerializer
from apps.core.response import detail_response
from apps.users.serializers.admin.admin_user_serializers import (
    AdminUserListQuerySerializer,
    AdminUserListSuccessResponseSerializer,
    AdminUserStatusUpdateRequestSerializer,
)
from apps.users.services.admin.admin_user_services import AdminUserService


@extend_schema(tags=["admin-accounts"])
class AdminUserListAPIView(AdminBaseAPIView):
    validation_error_msg = "잘못된 요청입니다."
    authentication_error_msg = "관리자 인증이 필요합니다."
    permission_error_msg = "권한이 없습니다."

    @extend_schema(
        summary="전체 사용자 목록 조회",
        parameters=[AdminUserListQuerySerializer],
        responses={
            200: AdminUserListSuccessResponseSerializer,
            400: ErrorDetailStringSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        serializer = AdminUserListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        users = AdminUserService.get_users(**serializer.validated_data)
        return detail_response(users, status.HTTP_200_OK)


@extend_schema(tags=["admin-accounts"])
class AdminUserStatusUpdateAPIView(AdminBaseAPIView):
    validation_error_msg = "잘못된 요청입니다."
    authentication_error_msg = "관리자 인증이 필요합니다."
    permission_error_msg = "권한이 없습니다."
    not_found_error_msg = "사용자를 찾을 수 없습니다."

    @extend_schema(
        summary="사용자 계정 상태 변경",
        request=AdminUserStatusUpdateRequestSerializer,
        responses={
            200: DetailMessageSerializer,
            400: ErrorDetailStringSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            404: ErrorDetailStringSerializer,
        },
    )
    def patch(self, request: Request, user_id: int) -> Response:
        serializer = AdminUserStatusUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AdminUserService.update_user_status(
            user_id=user_id,
            status_value=serializer.validated_data["status"],
            status_expires_at=serializer.validated_data.get("status_expires_at"),
            memo=serializer.validated_data.get("memo"),
        )
        return detail_response("사용자 계정 상태가 수정되었습니다.", status.HTTP_200_OK)
