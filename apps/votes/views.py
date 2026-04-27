from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from apps.core import ErrorDetailStringSerializer
from apps.core.exceptions import ConflictException, ResourceNotFoundException
from apps.core.response import detail_response, error_response
from apps.votes.serializers import (
    VoteCreateRequestSerializer,
    VoteCreateResponseSerializer,
    VoteDeleteResponseSerializer,
    VoteDetailSerializer,
    VoteParticipateResponseSerializer,
    VoteParticipateSerializer,
    VoteUpdateResponseSerializer,
    VoteUpdateSerializer,
)
from apps.votes.services import create_vote, delete_vote, get_vote_detail, participate_vote, update_vote


class VoteCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Votes"],
        summary="투표 생성",
        request=VoteCreateRequestSerializer,
        responses={
            200: VoteCreateResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={
                    "detail": {
                        "vote_id": 1,
                        "post_id": 10,
                        "question": "오늘 운동하셨나요?",
                        "start_at": "2026-04-20T09:00:00+09:00",
                        "end_at": "2026-04-27T09:00:00+09:00",
                        "status": "in_progress",
                        "options": [
                            {"vote_option_id": 1, "content": "예", "sort_order": 1},
                            {"vote_option_id": 2, "content": "아니오", "sort_order": 2},
                        ],
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request, post_id: int) -> Response:
        if not request.user.is_authenticated:
            return error_response("인증 정보가 없습니다.", 401)

        serializer = VoteCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("투표 입력값이 올바르지 않습니다.", 400)

        try:
            body = create_vote(
                post_id=post_id,
                question=serializer.validated_data["question"],
                options=serializer.validated_data["options"],
                start_at=serializer.validated_data["start_at"],
                end_at=serializer.validated_data["end_at"],
            )
        except NotFound:
            return error_response("해당 게시글을 찾을 수 없습니다.", 404)
        except ValidationError:
            return error_response("투표 입력값이 올바르지 않습니다.", 400)

        return detail_response(body, 200)


class VoteParticipateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Votes"],
        summary="투표 참여",
        request=VoteParticipateSerializer,
        responses={
            200: VoteParticipateResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={
                    "detail": {
                        "vote_id": 31,
                        "vote_option_id": 2,
                        "user_id": 12,
                        "created_at": "2026-04-08T14:30:00",
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request, vote_id: int) -> Response:
        if not request.user.is_authenticated:
            return error_response("인증 정보가 없습니다.", 401)

        serializer = VoteParticipateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, 400)

        try:
            body = participate_vote(
                vote_id=vote_id,
                user=request.user,
                option_id=serializer.validated_data["vote_option_id"],
            )
        except NotFound:
            return error_response("해당 투표를 찾을 수 없습니다.", 404)
        except ValidationError as e:
            msg = str(e)
            if "이미 참여한 투표입니다." in msg:
                return error_response("이미 참여한 투표입니다.", 409)
            if "유효한 투표 옵션이 필요합니다." in msg:
                return error_response("유효한 투표 옵션이 필요합니다.", 400)
            return error_response(msg, 400)

        return detail_response(body, 200)


class VoteDetailAPIView(APIView):
    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["Votes"],
        summary="투표 조회",
        responses={
            200: VoteDetailSerializer,
            404: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={
                    "detail": {
                        "vote_id": 31,
                        "status": "IN_PROGRESS",
                        "total_count": 20,
                        "options": [
                            {
                                "vote_option_id": 1,
                                "content": "운동",
                                "count": 8,
                                "rate": 40.0,
                            },
                            {
                                "vote_option_id": 2,
                                "content": "공부",
                                "count": 12,
                                "rate": 60.0,
                            },
                        ],
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "404 Not Found",
                value={"error_detail": "해당 투표를 찾을 수 없습니다."},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def get(self, request: Request, vote_id: int) -> Response:
        try:
            body = get_vote_detail(vote_id=vote_id)
        except NotFound:
            return error_response("해당 투표를 찾을 수 없습니다.", 404)

        return detail_response(body, 200)

    @extend_schema(
        tags=["Votes"],
        summary="투표 수정",
        request=VoteUpdateSerializer,
        responses={
            200: VoteUpdateResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={
                    "detail": {
                        "vote_id": 1,
                        "question": "수정된 질문입니다",
                        "start_at": "2026-04-20T09:00:00+09:00",
                        "end_at": "2026-04-27T09:00:00+09:00",
                        "status": "in_progress",
                        "options": [
                            {"vote_option_id": 1, "content": "예", "sort_order": 1},
                            {"vote_option_id": 2, "content": "아니오", "sort_order": 2},
                        ],
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def patch(self, request: Request, vote_id: int) -> Response:
        if not request.user.is_authenticated:
            return error_response("인증 정보가 없습니다.", 401)

        serializer = VoteUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, 400)

        try:
            body = update_vote(
                vote_id=vote_id,
                user=request.user,
                question=serializer.validated_data["question"],
                options=serializer.validated_data["options"],
                start_at=serializer.validated_data["start_at"],
                end_at=serializer.validated_data["end_at"],
            )
        except NotFound:
            return error_response("해당 투표를 찾을 수 없습니다.", 404)
        except ValidationError as e:
            msg = str(e)
            if "투표를 수정할 권한이 없습니다." in msg:
                return error_response(msg, 403)
            if (
                "이미 참여자가 있는 투표은 수정할 수 없습니다." in msg
                or "이미 참여자가 있는 투표는 수정할 수 없습니다." in msg
            ):
                return error_response("이미 참여자가 있는 투표는 수정할 수 없습니다.", 409)
            return error_response(msg, 400)

        return detail_response(body, 200)

    @extend_schema(
        tags=["Votes"],
        summary="투표 삭제",
        responses={
            200: VoteDeleteResponseSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            404: ErrorDetailStringSerializer,
            409: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={"detail": "투표가 삭제되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "401 Unauthorized",
                value={"error_detail": "인증 정보가 없습니다."},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "403 Forbidden",
                value={"error_detail": "투표를 삭제할 권한이 없습니다."},
                response_only=True,
                status_codes=["403"],
            ),
            OpenApiExample(
                "404 Not Found",
                value={"error_detail": "해당 투표를 찾을 수 없습니다."},
                response_only=True,
                status_codes=["404"],
            ),
            OpenApiExample(
                "409 Conflict",
                value={"error_detail": "이미 삭제된 투표입니다."},
                response_only=True,
                status_codes=["409"],
            ),
        ],
    )
    def delete(self, request: Request, vote_id: int) -> Response:
        if not request.user.is_authenticated:
            return error_response("인증 정보가 없습니다.", 401)

        try:
            delete_vote(vote_id=vote_id, user=request.user)
        except ResourceNotFoundException:
            return error_response("해당 투표를 찾을 수 없습니다.", 404)
        except ConflictException:
            return error_response("이미 삭제된 투표입니다.", 409)
        except ValidationError as e:
            msg = str(e)
            if "투표를 삭제할 권한이 없습니다." in msg:
                return error_response("투표를 삭제할 권한이 없습니다.", 403)
            return error_response(msg, 400)

        return detail_response("투표가 삭제되었습니다.", 200)
