from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.goals.models import Goal
from apps.goals.serializers.goal_create import (
    ErrorDetailSerializer,
    GoalCreateSerializer,
    GoalReadSerializer,
    GoalUpdateSerializer,
)
from apps.goals.services.goal_create import GoalCreateService


class GoalCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Goals"],
        summary="목표 생성",
        request=GoalCreateSerializer,
        responses={201: GoalReadSerializer, 400: ErrorDetailSerializer},
        examples=[
            OpenApiExample(
                "날짜 검증 에러 (400)",
                value={"error_detail": {"startDate": ["..."]}},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = GoalCreateSerializer(data=request.data)
        if serializer.is_valid():
            goal = GoalCreateService.create_goal(user=request.user, **serializer.validated_data)
            return Response(GoalCreateSerializer(goal).data, status=status.HTTP_201_CREATED)
        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Goals"],
        summary="전체 목표 목록 조회",
        description="로그인한 유저의 모든 목표를 최신순으로 조회합니다.",
        request=GoalReadSerializer,
        responses={200: GoalReadSerializer(many=True), 401: ErrorDetailSerializer},
        examples=[
            OpenApiExample(
                "401 인증 만료",
                value={"error_detail": {"Authorization": ["인증 토큰이 만료 되었습니다."]}},
                status_codes=["401"],
            )
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        goals = Goal.objects.filter(user=request.user.id).order_by("-created_at")
        serializer = GoalReadSerializer(goals, many=True)
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
            # 👈 404 예시 추가
            OpenApiExample(
                "404 조회 실패 (삭제되었거나 존재하지 않음)",
                value={"error_detail": {"goalId": ["존재하지 않거나 이미 삭제된 목표입니다."]}},
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
            200: GoalUpdateSerializer,
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "400 타입 오류",
                value={"error_detail": {"targetCount": ["목표 횟수는 숫자여야 합니다."]}},
                status_codes=["400"],
            ),
            OpenApiExample(
                "401 인증 오류",
                value={"error_detail": {"Authorization": ["인증 토큰이 올바르지 않습니다."]}},
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 수정 대상 없음",
                value={"error_detail": {"goalId": ["수정할 목표를 찾을 수 없습니다."]}},
                status_codes=["404"],
            ),
        ],
    )
    def patch(self, request: Request, goal_id: int) -> Response:
        goal = GoalCreateService.get_goal(goal_id, request.user)
        serializer = GoalCreateSerializer(goal, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_goal = GoalCreateService.update_goal(goal, **serializer.validated_data)
                return Response(GoalCreateSerializer(updated_goal).data, status=status.HTTP_200_OK)
            except PermissionError as e:
                return Response({"error_detail": {"detail": [str(e)]}}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Goals"],
        summary="목표 삭제",
        description="유저가 등록한 목표를 삭제합니다.",
        responses={204: OpenApiExample("성공", value=None), 401: ErrorDetailSerializer, 404: ErrorDetailSerializer},
        examples=[
            OpenApiExample(
                "401 인증 오류",
                value={"error_detail": {"Authorization": ["인증 토큰이 유효하지 않습니다."]}},
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 삭제 대상 없음",
                value={"error_detail": {"goalId": ["존재하지 않거나 이미 삭제된 목표입니다."]}},
                status_codes=["404"],
            ),
        ],
    )
    def delete(self, request: Request, goal_id: int, *args: Any, **kwargs: Any) -> Response:
        goal = GoalCreateService.get_goal(goal_id, request.user)
        GoalCreateService.delete_goal(goal)
        return Response({"detail": "목표가 성공적으로 삭제되었습니다."}, status=status.HTTP_200_OK)
