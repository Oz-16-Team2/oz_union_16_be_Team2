from __future__ import annotations

from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.goals.serializers.achievement import AchievementQuerySerializer, AchievementResponseSerializer
from apps.goals.services.achievement import AchievementService


@extend_schema(tags=["Goals"])
class AchievementView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="연별 달성 현황 조회 ",
        description="start ~ end 기간의 날짜별 목표 체크 횟수를 반환합니다. (깃허브 잔디 형태)",
        parameters=[
            OpenApiParameter(name="start", type=str, required=True, description="조회 시작일 (YYYY-MM-DD)"),
            OpenApiParameter(name="end", type=str, required=True, description="조회 종료일 (YYYY-MM-DD)"),
        ],
        responses={200: AchievementResponseSerializer, 400: None, 401: None},
        examples=[
            OpenApiExample(
                "조회 성공",
                value={
                    "detail": {
                        "start": "2026-01-01",
                        "end": "2026-12-31",
                        "days": [
                            {"date": "2026-01-01", "check_count": 0},
                            {"date": "2026-04-23", "check_count": 3},
                        ],
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "잘못된 날짜",
                value={"error_detail": "유효한 조회 기간이 필요합니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "인증 오류",
                value={"error_detail": "인증 정보가 없습니다."},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AchievementQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            print(serializer.errors)
            return Response(
                {"error_detail": "유효한 조회 기간이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start = serializer.validated_data["start"]
        end = serializer.validated_data["end"]
        days = AchievementService.get_achievement(user=request.user, start=start, end=end)

        return Response(
            {"detail": {"start": start, "end": end, "days": days}},
            status=status.HTTP_200_OK,
        )
