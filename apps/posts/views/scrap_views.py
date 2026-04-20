from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ConflictException
from apps.posts.models import Post, Scrap
from apps.posts.serializers.scrap_serializers import ScrapListSerializer


class PostScrapView(APIView):
    """
    REQ-SCRP-001 (POST): 스크랩 생성
    REQ-SCRP-003 (DELETE): 스크랩 취소
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="게시글 스크랩", responses={201: None}, tags=["스크랩 (Scraps)"])
    def post(self, request: Request, post_id: int) -> Response:
        if not Post.objects.filter(id=post_id).exists():
            raise NotFound("게시글을 찾을 수 없습니다.")

        user_id = cast(int, request.user.id)
        scrap, created = Scrap.objects.get_or_create(user_id=user_id, post_id=post_id)

        if not created:
            raise ConflictException("이미 스크랩한 게시글입니다.")

        return Response(status=status.HTTP_201_CREATED)

    @extend_schema(summary="게시글 스크랩 취소", responses={204: None}, tags=["스크랩 (Scraps)"])
    def delete(self, request: Request, post_id: int) -> Response:
        user_id = cast(int, request.user.id)
        deleted, _ = Scrap.objects.filter(user_id=user_id, post_id=post_id).delete()

        if not deleted:
            raise NotFound("스크랩 기록을 찾을 수 없습니다.")

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserScrapListView(APIView):
    """
    REQ-SCRP-002 (GET): 내 스크랩 목록 조회
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="내 스크랩 목록 조회", responses=ScrapListSerializer(many=True), tags=["스크랩 (Scraps)"])
    def get(self, request: Request) -> Response:
        user_id = cast(int, request.user.id)

        # select_related('post'), N+1 방지
        scraps = Scrap.objects.filter(user_id=user_id).select_related("post").order_by("-created_at")

        # TODO: 페이지네이션(Pagination) 처리가 필요하다면 이 부분에 추가
        total_count = scraps.count()
        serializer = ScrapListSerializer(scraps, many=True)

        return Response({"total_count": total_count, "results": serializer.data}, status=status.HTTP_200_OK)
