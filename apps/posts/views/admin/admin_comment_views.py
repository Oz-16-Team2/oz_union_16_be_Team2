from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core import DetailMessageSerializer, ErrorDetailStringSerializer, detail_response
from apps.core.admin import AdminBaseAPIView
from apps.posts.services.admin.admin_comment_services import AdminCommentService


class AdminCommentDeleteAPIView(AdminBaseAPIView):
    @extend_schema(
        tags=["admin-comments"],
        responses={
            200: DetailMessageSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            404: ErrorDetailStringSerializer,
        },
    )
    def delete(self, request: Request, comment_id: int) -> Response:
        AdminCommentService.delete_comment(comment_id=comment_id)
        return detail_response("댓글이 삭제되었습니다.", status.HTTP_200_OK)