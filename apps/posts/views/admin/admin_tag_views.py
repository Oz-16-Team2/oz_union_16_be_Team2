from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core import DetailMessageSerializer, ErrorDetailStringSerializer, detail_response
from apps.core.admin import AdminBaseAPIView, IsAdminRole
from apps.posts.serializers.admin.admin_tag_serializers import (
    AdminTagCreateRequestSerializer,
    AdminTagListQuerySerializer,
    AdminTagListSuccessResponseSerializer,
    AdminTagResponseSerializer,
    AdminTagUpdateRequestSerializer,
)
from apps.posts.services.admin.admin_tag_services import AdminTagService


class AdminTagListCreateAPIView(AdminBaseAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @extend_schema(
        tags=["admin-tags"],
        parameters=[
            OpenApiParameter(name="page", required=True, type=int),
            OpenApiParameter(name="size", required=True, type=int),
        ],
        responses={
            200: AdminTagListSuccessResponseSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        query_serializer = AdminTagListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        tags = AdminTagService.get_tags(
            page=query_serializer.validated_data["page"],
            size=query_serializer.validated_data["size"],
        )

        response_serializer = AdminTagResponseSerializer(tags, many=True)

        return detail_response(response_serializer.data, status.HTTP_200_OK)

    @extend_schema(
        tags=["admin-tags"],
        request=AdminTagCreateRequestSerializer,
        responses={
            201: DetailMessageSerializer,
            400: ErrorDetailStringSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            409: ErrorDetailStringSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = AdminTagCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AdminTagService.create_tag(
            name=serializer.validated_data["name"],
        )

        return detail_response("태그가 생성되었습니다.", status.HTTP_201_CREATED)


class AdminTagUpdateAPIView(AdminBaseAPIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    @extend_schema(
        tags=["admin-tags"],
        request=AdminTagUpdateRequestSerializer,
        responses={
            200: DetailMessageSerializer,
            400: ErrorDetailStringSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            404: ErrorDetailStringSerializer,
        },
    )
    def patch(self, request: Request, tag_id: int) -> Response:
        serializer = AdminTagUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AdminTagService.update_tag_status(
            tag_id=tag_id,
            is_active=serializer.validated_data["is_active"],
        )

        return detail_response("태그 상태가 수정되었습니다.", status.HTTP_200_OK)
