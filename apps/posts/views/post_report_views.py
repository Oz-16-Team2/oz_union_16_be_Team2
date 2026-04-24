from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.response import detail_response, error_response
from apps.goals.serializers.goal_create import ErrorDetailSerializer
from apps.posts.serializers.post_report_serializers import (
    PostReportCreateResponseSerializer,
    PostReportCreateSerializer,
)
from apps.posts.services.post_report_service import create_post_report


class PostReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Posts"],
        summary="게시글 신고 (REQ-POST-006)",
        description="로그인한 유저가 특정 게시글을 신고합니다.",
        request=PostReportCreateSerializer,
        responses={
            201: PostReportCreateResponseSerializer,
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "신고 성공 (201)",
                value={
                    "detail": "신고가 정상적으로 접수(인스턴스 생성)되었습니다.",
                    "report_id": 12,
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "400 - 잘못된 신고 유형",
                value={"error_detail": {"reason_type": ["올바른 신고 사유 유형을 선택해 주세요."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "400 - 중복 신고",
                value={"error_detail": {"detail": ["이미 신고한 게시글입니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "401 인증 실패",
                value={"error_detail": {"Authorization": ["로그인이 필요한 서비스입니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 게시글 없음",
                value={"error_detail": {"postId": ["신고하려는 게시글을 찾을 수 없습니다."]}},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def post(self, request: Request, post_id: int) -> Response:
        if not request.user.is_authenticated:
            return error_response({"Authorization": ["로그인이 필요한 서비스입니다."]}, 401)

        serializer = PostReportCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response({"reason_type": ["올바른 신고 유형을 선택해주세요"]}, 400)

        try:
            report = create_post_report(
                user=request.user,
                post_id=post_id,
                reason_type=serializer.validated_data["reason_type"],
                reason_detail=serializer.validated_data.get("reason_detail"),
            )
        except NotFound as e:
            return error_response(e.detail, 404)
        except ValidationError as e:
            return error_response(e.detail, 400)

        data = {"detail": "신고가 정상적으로 접수되었습니다", "report_id": report.id}
        response_serializer = PostReportCreateResponseSerializer(instance=data)
        return Response(response_serializer.data, status=201)
