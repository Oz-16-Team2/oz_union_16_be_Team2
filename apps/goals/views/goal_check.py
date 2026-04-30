from typing import Any, cast

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.goals.serializers.goal_create import (
    ErrorDetailSerializer,
    GoalCheckSerializer,
    GoalReadSerializer,
)
from apps.goals.services.goal_check import GoalCheckService
from apps.goals.services.goal_create import GoalCreateService
from apps.users.models import User


class GoalPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = "size"
    page_query_param = "page"


class GoalCheckView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Goals"],
        summary="오늘의 목표 달성 인증",
        description="특정 목표에 대해 오늘치 인증을 기록합니다. 자정이 지나면 다시 인증할 수 있습니다.",
        responses={
            200: GoalCheckSerializer,
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "인증 성공",
                value={"detail": "오늘의 목표 달성 인증이 완료되었습니다.", "goal_id": 101, "progress_rate": 25.0},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "400 중복 인증 오류",
                value={"error_detail": {"detail": ["오늘 이미 인증을 완료했습니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "400 기간 외 인증 오류",
                value={"error_detail": {"detail": ["목표 기간이 아닙니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "401 인증 오류",
                value={"error_detail": {"detail": ["자격 인증 데이터가 제공되지 않았습니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 목표 없음",
                value={"error_detail": {"detail": ["존재하지 않거나 접근 권한이 없는 목표입니다."]}},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def post(self, request: Request, goal_id: int) -> Response:
        try:
            result = GoalCheckService.check_goal_today(goal_id, request.user)
            serializer = GoalCheckSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error_detail": {"detail": [str(e)]}}, status=status.HTTP_400_BAD_REQUEST)


class GoalCheckedHistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Goals"],
        summary="특정 날짜 인증 목표 목록 조회 (잔디 클릭)",
        description="잔디 그래프에서 특정 날짜를 클릭했을 때, 해당 날짜에 인증 기록이 있는 목표들의 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(name="date", type=str, description="조회할 날짜 (YYYY-MM-DD 형식, 필수)", required=True),
            OpenApiParameter(name="page", type=int, description="페이지 번호", required=False),
            OpenApiParameter(name="size", type=int, description="페이지당 개수", required=False),
        ],
        responses={
            200: inline_serializer(
                name="PaginatedGoalHistoryResponse",
                fields={
                    "count": drf_serializers.IntegerField(),
                    "next": drf_serializers.URLField(allow_null=True),
                    "previous": drf_serializers.URLField(allow_null=True),
                    "results": GoalReadSerializer(many=True),
                },
            ),
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "성공 응답 (200)",
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "goal_id": 1,
                            "title": "물 2L 마시기",
                            "start_date": "2026-04-14",
                            "end_date": "2026-05-14",
                            "status": "COMPLETED",
                            "created_at": "2026-04-14T19:00:00",
                            "progress_rate": 100.0,
                            "is_checked_today": True,
                        }
                    ],
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "날짜 누락 에러 (400)",
                value={"error_detail": {"date": ["날짜(date) 파라미터가 필요합니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)
        target_date = request.query_params.get("date")

        if not target_date:
            return Response(
                {"error_detail": {"date": ["날짜(date) 쿼리 파라미터가 필요합니다. (예: ?date=2026-04-17)"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = GoalCreateService.get_checked_goals_by_date(user=user, target_date=target_date)

        paginator = GoalPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        if paginated_queryset is not None:
            serializer = GoalReadSerializer(paginated_queryset, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)

        serializer = GoalReadSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
