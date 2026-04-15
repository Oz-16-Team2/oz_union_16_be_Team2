from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core import DetailMessageSerializer, ErrorDetailStringSerializer, detail_response
from apps.core.admin import AdminBaseAPIView
from apps.posts.serializers.admin.admin_post_serializers import (
    AdminPostDetailSuccessResponseSerializer,
    AdminPostListQuerySerializer,
    AdminPostListSuccessResponseSerializer,
    AdminPostStatusUpdateRequestSerializer,
)
from apps.posts.services.admin.admin_post_services import AdminPostService


class AdminPostListAPIView(AdminBaseAPIView):
    @extend_schema(
        tags=["admin-posts"],
        parameters=[
            OpenApiParameter(name="users_id", required=False, type=int),
            OpenApiParameter(name="status", required=False, type=str),
            OpenApiParameter(name="has_goal", required=False, type=bool),
            OpenApiParameter(name="has_vote", required=False, type=bool),
            OpenApiParameter(name="page", required=True, type=int),
            OpenApiParameter(name="size", required=True, type=int),
        ],
        responses={
            200: AdminPostListSuccessResponseSerializer,
            400: ErrorDetailStringSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        serializer = AdminPostListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        has_goal = serializer.validated_data.get("has_goal") if "has_goal" in request.query_params else None
        has_vote = serializer.validated_data.get("has_vote") if "has_vote" in request.query_params else None

        posts = AdminPostService.get_posts(
            user_id=serializer.validated_data.get("users_id"),
            status_value=serializer.validated_data.get("status"),
            has_goal=has_goal,
            has_vote=has_vote,
            page=serializer.validated_data["page"],
            size=serializer.validated_data["size"],
        )
        return detail_response(posts, status.HTTP_200_OK)


class AdminPostDetailAPIView(AdminBaseAPIView):
    @extend_schema(
        tags=["admin-posts"],
        responses={
            200: AdminPostDetailSuccessResponseSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            404: ErrorDetailStringSerializer,
        },
    )
    def get(self, request: Request, post_id: int) -> Response:
        post_detail = AdminPostService.get_post_detail(post_id=post_id)
        return detail_response(post_detail, status.HTTP_200_OK)


class AdminPostDeleteAPIView(AdminBaseAPIView):
    @extend_schema(
        tags=["admin-posts"],
        responses={
            200: DetailMessageSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            404: ErrorDetailStringSerializer,
        },
    )
    def delete(self, request: Request, post_id: int) -> Response:
        AdminPostService.delete_post(post_id=post_id)
        return detail_response("게시글이 삭제되었습니다.", status.HTTP_200_OK)


class AdminPostStatusUpdateAPIView(AdminBaseAPIView):
    @extend_schema(
        tags=["admin-posts"],
        request=AdminPostStatusUpdateRequestSerializer,
        responses={
            200: DetailMessageSerializer,
            400: ErrorDetailStringSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            404: ErrorDetailStringSerializer,
        },
    )
    def patch(self, request: Request, post_id: int) -> Response:
        serializer = AdminPostStatusUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AdminPostService.update_post_status(
            post_id=post_id,
            status_value=serializer.validated_data["status"],
        )
        return detail_response("게시글 상태가 수정되었습니다.", status.HTTP_200_OK)
