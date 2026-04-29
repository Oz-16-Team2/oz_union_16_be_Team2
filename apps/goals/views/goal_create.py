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
    GoalCreateSerializer,
    GoalReadSerializer,
    GoalUpdateSerializer,
)
from apps.goals.services.goal_create import GoalCreateService
from apps.users.models import User


class GoalPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = "size"
    page_query_param = "page"


class GoalCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Goals"],
        summary="목표 생성",
        description="로그인한 유저가 목표를 생성합니다.",
        request=GoalCreateSerializer,
        responses={201: GoalReadSerializer, 400: ErrorDetailSerializer},
        examples=[
            OpenApiExample(
                "생성 성공 예시",
                value={
                    "goal_id": 1,
                    "title": "매일 물 2L 마시기",
                    "start_date": "2026-04-14",
                    "end_date": "2026-05-14",
                    "status": "IN_PROGRESS",
                    "created_at": "2026-04-14T19:00:00",
                    "progress_rate": 0.0,
                    "is_checked_today": False,
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "날짜 검증 에러 (400)",
                value={"error_detail": {"start_date": ["종료일은 시작일보다 빠를 수 없습니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = GoalCreateSerializer(data=request.data)
        if serializer.is_valid():
            goal = GoalCreateService.create_goal(user=request.user, **serializer.validated_data)
            return Response(GoalReadSerializer(goal).data, status=status.HTTP_201_CREATED)
        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Goals"],
        summary="전체 목표 목록 조회 (필터링 및 페이지네이션)",
        description="유저의 목표를 최신순으로 조회합니다. 상태별 필터링 및 시작/종료일 기간 필터링이 가능합니다.",
        parameters=[
            OpenApiParameter(
                name="status", type=str, description="in_progress, failed, completed 중 하나", required=False
            ),
            OpenApiParameter(name="start", type=str, description="조회 시작일 (YYYY-MM-DD)", required=False),
            OpenApiParameter(name="end", type=str, description="조회 종료일 (YYYY-MM-DD)", required=False),
            OpenApiParameter(name="page", type=int, description="페이지 번호", required=False),
            OpenApiParameter(name="size", type=int, description="페이지당 개수", required=False),
        ],
        responses={
            200: inline_serializer(
                name="PaginatedGoalListResponse",
                fields={
                    "count": drf_serializers.IntegerField(),
                    "next": drf_serializers.URLField(allow_null=True),
                    "previous": drf_serializers.URLField(allow_null=True),
                    "results": GoalReadSerializer(many=True),
                },
            ),
            401: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "성공 응답 예시",
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "goal_id": 1,
                            "title": "필터링된 목표",
                            "startDate": "2026-04-14",
                            "endDate": "2026-05-14",
                            "status": "IN_PROGRESS",
                            "created_at": "2026-04-14T19:00:00",
                            "progressRate": 10,
                            "isCheckedToday": False,
                        }
                    ],
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)

        queryset = GoalCreateService.get_goal_list(
            user=user,
            status_filter=request.query_params.get("status"),
            start_date_filter=request.query_params.get("start"),
            end_date_filter=request.query_params.get("end"),
        )

        paginator = GoalPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        if paginated_queryset is not None:
            serializer = GoalReadSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = GoalReadSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GoalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Goals"],
        summary="목표 상세 조회",
        description="목표 리스트에서 하나를 클릭했을 때 나타나는 상세 정보를 조회합니다.",
        request=GoalReadSerializer,
        responses={
            200: GoalReadSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "401 인증 만료",
                value={"error_detail": {"Authorization": ["인증 토큰이 만료 되었습니다."]}},
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 조회 실패",
                value={"error_detail": {"goal_id": ["존재하지 않거나 이미 삭제된 목표입니다."]}},
                status_codes=["404"],
            ),
        ],
    )
    def get(self, request: Request, goal_id: int, *args: Any, **kwargs: Any) -> Response:
        goal = GoalCreateService.get_goal(goal_id, request.user)
        return Response(GoalReadSerializer(goal).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Goals"],
        summary="목표 수정",
        description="유저가 등록한 목표를 수정합니다.",
        request=GoalUpdateSerializer,
        responses={
            200: GoalReadSerializer,
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "목표 수정 데이터 예시",
                value={"title": "수정된 제목"},
                request_only=True,
            ),
            OpenApiExample(
                "401 인증 오류",
                value={"error_detail": {"Authorization": ["인증 토큰이 올바르지 않습니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 수정 대상 없음",
                value={"error_detail": {"goal_id": ["수정할 목표를 찾을 수 없습니다."]}},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def patch(self, request: Request, goal_id: int) -> Response:
        goal = GoalCreateService.get_goal(goal_id, request.user)
        serializer = GoalUpdateSerializer(goal, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_goal = GoalCreateService.update_goal(goal, **serializer.validated_data)
                return Response(GoalReadSerializer(updated_goal).data, status=status.HTTP_200_OK)
            except PermissionError as e:
                return Response({"error_detail": {"detail": [str(e)]}}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Goals"],
        summary="목표 삭제",
        description="유저가 등록한 목표를 삭제합니다.",
        responses={
            200: inline_serializer(name="DeleteSuccess", fields={"detail": drf_serializers.CharField()}),
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "삭제 성공",
                value={"detail": "목표가 성공적으로 삭제되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "401 인증 오류",
                value={"error_detail": {"Authorization": ["인증 토큰이 유효하지 않습니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 삭제 대상 없음",
                value={"error_detail": {"goalId": ["존재하지 않거나 이미 삭제된 목표입니다."]}},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def delete(self, request: Request, goal_id: int, *args: Any, **kwargs: Any) -> Response:
        goal = GoalCreateService.get_goal(goal_id, request.user)
        GoalCreateService.delete_goal(goal)
        return Response({"detail": "목표가 성공적으로 삭제되었습니다."}, status=status.HTTP_200_OK)
