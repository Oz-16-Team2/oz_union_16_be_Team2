from typing import cast

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import parsers, status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.response import detail_response
from apps.users.models import User
from apps.users.serializers.auth_serializers import ChangePasswordSerializer
from apps.users.serializers.common_serializers import (
    ErrorDetailFieldListSerializer,
    ErrorDetailStringSerializer,
    MessageResponseSerializer,
)
from apps.users.serializers.profile_serializers import (
    MeActivitySummaryAchievementRateResponseSerializer,
    MeActivitySummaryCompletedGoalsResponseSerializer,
    MeActivitySummaryDaysResponseSerializer,
    ProfileImageListResponseSerializer,
    UserProfileSerializer,
)
from apps.users.services.auth_services import change_password
from apps.users.services.profile_services import (
    ProfileService,
    get_me_activity_summary_achievement_rate,
    get_me_activity_summary_completed_goals,
    get_me_activity_summary_days,
    get_my_profile,
)


@extend_schema(tags=["Accounts"])
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 프로필 조회",
        responses={200: UserProfileSerializer},
        examples=[
            OpenApiExample(
                "내 프로필 조회 성공",
                value={
                    "id": 1,
                    "nickname": "testnick",
                    "profile_image_url": "https://example.com/profile.png",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        return Response(get_my_profile(request.user), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class MeActivitySummaryDaysAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="함께한 기간",
        responses={200: MeActivitySummaryDaysResponseSerializer, 401: ErrorDetailStringSerializer},
        examples=[
            OpenApiExample(
                "함께한 기간 성공",
                value={"detail": {"days_together": 120}},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "인증 실패",
                value={"error_detail": "인증 정보가 없습니다."},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        return Response(get_me_activity_summary_days(request.user), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class MeActivitySummaryAchievementRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="전체 달성률",
        responses={200: MeActivitySummaryAchievementRateResponseSerializer, 401: ErrorDetailStringSerializer},
        examples=[
            OpenApiExample(
                "전체 달성률 성공",
                value={
                    "detail": {
                        "total_goals_count": 24,
                        "completed_goals_count": 18,
                        "total_achievement_rate": 75.0,
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "인증 실패",
                value={"error_detail": "인증 정보가 없습니다."},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        return Response(get_me_activity_summary_achievement_rate(request.user), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class MeActivitySummaryCompletedGoalsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="완료한 일정",
        responses={200: MeActivitySummaryCompletedGoalsResponseSerializer, 401: ErrorDetailStringSerializer},
        examples=[
            OpenApiExample(
                "완료한 일정 성공",
                value={"detail": {"completed_goals_count": 18}},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "인증 실패",
                value={"error_detail": "인증 정보가 없습니다."},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        return Response(get_me_activity_summary_completed_goals(request.user), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class ChangePasswordAPIView(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="비밀번호 변경",
        request=ChangePasswordSerializer,
        responses={
            200: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "비밀번호 변경 성공",
                value={"detail": "비밀번호가 변경되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "비밀번호 변경 실패 - 형식/검증 오류",
                value={
                    "error_detail": {
                        "new_password": ["비밀번호 형식이 올바르지 않습니다."],
                        "new_password_confirm": ["비밀번호가 일치하지 않습니다."],
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "비밀번호 변경 실패 - 인증 필요",
                value={"error_detail": "로그인 인증이 필요합니다."},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "비밀번호 변경 실패 - 기존 비밀번호 불일치",
                value={"error_detail": "기존 비밀번호가 일치하지 않습니다."},
                response_only=True,
                status_codes=["403"],
            ),
        ],
    )
    def patch(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = change_password(
            user=cast(User, request.user),
            password=serializer.validated_data["password"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class ProfileImageListAPIView(APIView):
    permission_classes = []

    @extend_schema(
        summary="프로필 이미지 목록 조회",
        responses={200: ProfileImageListResponseSerializer},
        examples=[
            OpenApiExample(
                "프로필 이미지 목록 조회 성공",
                value={
                    "detail": [
                        {
                            "code": "avatar_01",
                            "image_url": "https://example.com/profile/avatar_01.png",
                        },
                        {
                            "code": "avatar_02",
                            "image_url": "https://example.com/profile/avatar_02.png",
                        },
                    ]
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        data = ProfileService.get_profile_images()
        return detail_response(data, status.HTTP_200_OK)
