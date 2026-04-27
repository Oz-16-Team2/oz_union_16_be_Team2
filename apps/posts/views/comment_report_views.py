from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.response import detail_response, error_response
from apps.posts.serializers.post_report_serializers import PostReportCreateSerializer
from apps.posts.services.comment_report_service import create_comment_report


class CommentReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["댓글 (Comments)"],
        summary="댓글 신고",
        description="로그인한 유저가 특정 댓글을 신고합니다.",
        request=PostReportCreateSerializer,
        responses={
            200: dict,
            400: dict,
            409: dict,
        },
    )
    def post(self, request: Request, comment_id: int) -> Response:
        serializer = PostReportCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        try:
            create_comment_report(
                user=request.user,
                comment_id=comment_id,
                reason_type=serializer.validated_data["reason_type"],
                reason_detail=serializer.validated_data.get("reason_detail"),
            )
        except NotFound as e:
            return error_response(e.detail, status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return error_response(e.detail, status.HTTP_409_CONFLICT)

        return detail_response({"detail": "댓글 신고가 정상적으로 접수되었습니다."}, status.HTTP_200_OK)
