from __future__ import annotations

from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.goals.serializers.ranking import (
    MonthlyRankingResponseSerializer,
    TotalRankingResponseSerializer,
    WeeklyRankingResponseSerializer,
)
from apps.goals.services.ranking import get_monthly_ranking, get_total_ranking, get_weekly_ranking


@extend_schema(tags=["Ranking"])
class WeeklyRankingView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="주 랭킹 조회",
        description="오늘 날짜 기준 이번 주(월요일~일요일) 랭킹을 반환합니다.",
        responses={200: WeeklyRankingResponseSerializer},
        examples=[
            OpenApiExample(
                "주 랭킹 조회 성공",
                value={
                    "detail": {
                        "rankings": [
                            {
                                "user_id": 1,
                                "nickname": "유저1",
                                "profile_img_url": "https://...",
                                "rank": 1,
                                "week_cert_count": 20,
                            }
                        ]
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        rankings = get_weekly_ranking()
        return Response({"detail": {"rankings": rankings}}, status=status.HTTP_200_OK)


@extend_schema(tags=["Ranking"])
class MonthlyRankingView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="월 랭킹 조회",
        description="오늘 날짜 기준 이번 달 랭킹을 반환합니다.",
        responses={200: MonthlyRankingResponseSerializer},
        examples=[
            OpenApiExample(
                "월 랭킹 조회 성공",
                value={
                    "detail": {
                        "rankings": [
                            {
                                "user_id": 1,
                                "nickname": "유저1",
                                "profile_img_url": "https://...",
                                "rank": 1,
                                "month_cert_count": 20,
                            }
                        ]
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        rankings = get_monthly_ranking()
        return Response({"detail": {"rankings": rankings}}, status=status.HTTP_200_OK)


@extend_schema(tags=["Ranking"])
class TotalRankingView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="누적 랭킹 조회",
        responses={200: TotalRankingResponseSerializer},
        examples=[
            OpenApiExample(
                "누적 랭킹 조회 성공",
                value={
                    "detail": {
                        "rankings": [
                            {
                                "user_id": 1,
                                "nickname": "유저1",
                                "profile_img_url": "https://...",
                                "rank": 1,
                                "total_cert_count": 20,
                            }
                        ]
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        rankings = get_total_ranking()
        return Response({"detail": {"rankings": rankings}}, status=status.HTTP_200_OK)
