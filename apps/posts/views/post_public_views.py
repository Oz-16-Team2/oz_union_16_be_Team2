from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import parsers, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import error_response
from apps.goals.serializers.goal_create import ErrorDetailSerializer
from apps.posts.serializers.post_serializers import (
    SCOPE_MY,
    MessageDetailSerializer,
    PostCreateResponseSerializer,
    PostCreateSerializer,
    PostDetailSerializer,
    PostFeedResponseSerializer,
    PostListQuerySerializer,
    PostPatchSerializer,
    PostSearchQuerySerializer,
    PostSearchResponseSerializer,
)
from apps.posts.services import (
    create_post,
    get_post_detail,
    list_posts,
    search_posts,
    soft_delete_post,
    update_post,
)

TAG_POSTS = "Posts"


class PostCollectionAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        tags=[TAG_POSTS],
        summary="포스트 목록 조회 (REQ-POST-001)",
        description=(
            "Query: scope (FEED|MY), sort_by (LATEST|POPULAR), page, size. "
            "Optional auth affects is_scrapped. MY requires login."
        ),
        parameters=[
            OpenApiParameter(
                name="scope",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="FEED (기본값) 또는 MY",
            ),
            OpenApiParameter(
                name="sort_by",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="LATEST (기본값) 또는 POPULAR",
            ),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="size", type=int, location=OpenApiParameter.QUERY, required=False, default=8),
        ],
        responses={
            200: PostFeedResponseSerializer,
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={
                    "posts": [
                        {
                            "post_id": 301,
                            "images": [],
                            "profile_image_url": "https://cdn.example.com/profiles/user-10.jpg",
                            "nickname": "user",
                            "created_at": "2026-04-08T00:00:00Z",
                            "title": "오늘의 운동",
                            "tags": ["workout", "running"],
                            "content_preview": "오늘 5km 뛰었습니다.",
                            "like_count": 15,
                            "comment_count": 4,
                            "is_scrapped": True,
                        }
                    ],
                    "page": 0,
                    "size": 8,
                    "total_count": 150,
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "400 validation",
                value={"error_detail": {"sortBy": ["정렬 기준이 올바르지 않습니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "401 unauthorized",
                value={"error_detail": {"Authorization": ["나의 게시물을 조회하려면 로그인이 필요합니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        q = PostListQuerySerializer(data=request.query_params)
        if not q.is_valid():
            return error_response(q.errors, status.HTTP_400_BAD_REQUEST)
        data = q.validated_data
        if data["scope"] == SCOPE_MY and not request.user.is_authenticated:
            return error_response(
                {"Authorization": ["나의 게시물을 조회하려면 로그인이 필요합니다."]},
                status.HTTP_401_UNAUTHORIZED,
            )
        try:
            body = list_posts(
                scope=data["scope"],
                sort_by=data["sort_by"],
                page=data["page"],
                size=data["size"],
                user=request.user,
            )
        except serializers.ValidationError as exc:
            return error_response(exc.detail, status.HTTP_400_BAD_REQUEST)

        response_serializer = PostFeedResponseSerializer(instance=body)
        return Response(response_serializer.data, status=200)

    @extend_schema(
        tags=[TAG_POSTS],
        summary="포스트 작성 (REQ-POST-003)",
        request=PostCreateSerializer,
        responses={
            201: PostCreateResponseSerializer,
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "201 Created",
                value={"detail": "게시글 작성이 완료되었습니다.", "post_id": 305},
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "400 validation",
                value={
                    "error_detail": {
                        "title": ["제목은 필수 입력 사항입니다."],
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "401 unauthorized",
                value={"error_detail": {"Authorization": ["인증 토큰(열쇠)이 유효하지 않습니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        if not request.user.is_authenticated:
            return error_response(
                {"Authorization": ["인증 토큰(열쇠)이 유효하지 않습니다."]},
                401,
            )
        ser = PostCreateSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(ser.errors, 400)
        try:
            post = create_post(request.user, ser.validated_data)
        except serializers.ValidationError as exc:
            return error_response(exc.detail, 400)

        data = {"detail": "게시글 작성이 완료되었습니다.", "post_id": post.id}
        if hasattr(post, "vote"):
            data["vote_id"] = post.vote.id
        response_serializer = PostCreateResponseSerializer(instance=data)
        return Response(response_serializer.data, status=201)


class PostDetailAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        tags=[TAG_POSTS],
        summary="포스트 상세 조회 (REQ-POST-005)",
        responses={
            200: PostDetailSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={
                    "post_id": 301,
                    "images": [],
                    "profile_image_url": "https://cdn.example.com/profiles/user-10.jpg",
                    "nickname": "user",
                    "created_at": "2026-04-08T00:00:00Z",
                    "title": "오늘의 운동",
                    "content": "오늘 5km 뛰었습니다.",
                    "tags": ["workout", "running"],
                    "like_count": 15,
                    "comment_count": 4,
                    "is_scrapped": False,
                    "has_goal": True,
                    "goal_info": {
                        "goal_id": 12,
                        "goal_title": "한 달 달리기",
                        "goal_start_date": "2026-04-01T00:00:00Z",
                        "goal_end_date": "2026-04-30T00:00:00Z",
                        "goal_progress": 40,
                    },
                    "has_vote": True,
                    "vote_info": {
                        "vote_id": 41,
                        "end_at": "2026-04-10T09:00:00Z",
                        "status": "in_progress",
                        "options": [
                            {"option_id": 101, "content": "처음 1km", "sort_order": 1},
                            {"option_id": 102, "content": "중간 언덕", "sort_order": 2},
                        ],
                    },
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "401 unauthorized",
                value={"error_detail": {"Authorization": ["인증 토큰(열쇠)이 유효하지 않습니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 not found",
                value={"error_detail": {"postId": ["해당 게시글을 찾을 수 없습니다."]}},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def get(self, request: Request, post_id: int) -> Response:
        try:
            body = get_post_detail(post_id=post_id, user=request.user)
        except serializers.ValidationError as exc:
            status_code: int = status.HTTP_400_BAD_REQUEST
            if "postId" in exc.detail:
                status_code = status.HTTP_404_NOT_FOUND
            return error_response(exc.detail, status_code)

        response_serializer = PostDetailSerializer(instance=body)
        return Response(response_serializer.data, status=200)

    @extend_schema(
        tags=[TAG_POSTS],
        summary="포스트 수정 (REQ-POST-002)",
        request=PostPatchSerializer,
        responses={
            200: MessageDetailSerializer,
            400: ErrorDetailSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={"detail": "게시글 수정이 완료되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "400 validation",
                value={"error_detail": {"tagIds": ["태그는 최대 3개까지만 등록 가능합니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "401 unauthorized",
                value={"error_detail": {"Authorization": ["인증 토큰(열쇠)이 유효하지 않습니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 not found",
                value={"error_detail": {"postId": ["해당 게시글을 찾을 수 없습니다."]}},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def patch(self, request: Request, post_id: int) -> Response:
        if not request.user.is_authenticated:
            return error_response({"Authorization": ["인증 토큰(열쇠)이 유효하지 않습니다."]}, 401)

        ser = PostPatchSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(ser.errors, 400)
        try:
            update_post(user=request.user, url_post_id=post_id, data=ser.validated_data)
        except serializers.ValidationError as exc:
            status_code: int = status.HTTP_400_BAD_REQUEST
            if "postId" in exc.detail:
                status_code = status.HTTP_404_NOT_FOUND
            elif "Authorization" in exc.detail:
                status_code = status.HTTP_401_UNAUTHORIZED
            return error_response(exc.detail, status_code)

        data = {"detail": "게시글 수정이 완료되었습니다."}
        response_serializer = MessageDetailSerializer(instance=data)
        return Response(response_serializer.data, status=200)

    @extend_schema(
        tags=[TAG_POSTS],
        summary="포스트 삭제 (REQ-POST-004)",
        responses={
            200: MessageDetailSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "200 OK",
                value={"detail": "게시글 삭제가 완료되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "401 unauthorized",
                value={"error_detail": {"Authorization": ["인증 토큰(열쇠)이 유효하지 않습니다."]}},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "404 not found",
                value={"error_detail": {"postId": ["해당 게시글을 찾을 수 없습니다."]}},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def delete(self, request: Request, post_id: int) -> Response:
        if not request.user.is_authenticated:
            return error_response({"Authorization": ["인증 토큰(열쇠)이 유효하지 않습니다."]}, 401)
        try:
            soft_delete_post(user=request.user, post_id=post_id)
        except serializers.ValidationError as exc:
            status_code: int = status.HTTP_400_BAD_REQUEST
            if "postId" in exc.detail:
                status_code = status.HTTP_404_NOT_FOUND
            elif "Authorization" in exc.detail:
                status_code = status.HTTP_401_UNAUTHORIZED
            return error_response(exc.detail, status_code)

        data = {"detail": "게시글 삭제가 완료되었습니다."}
        response_serializer = MessageDetailSerializer(instance=data)
        return Response(response_serializer.data, status=200)


class PostSearchAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=[TAG_POSTS],
        summary="포스트 검색",
        parameters=[
            OpenApiParameter(
                name="keyword",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="검색어 (최소 2글자)",
            ),
            OpenApiParameter(
                name="type",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="검색 타입: title (제목), content (내용), all (제목+내용, 기본값)",
            ),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY, default=0),
            OpenApiParameter(name="size", type=int, location=OpenApiParameter.QUERY, default=8),
        ],
        responses={200: PostSearchResponseSerializer, 400: ErrorDetailSerializer, 404: ErrorDetailSerializer},
    )
    def get(self, request: Request) -> Response:
        q = PostSearchQuerySerializer(data=request.query_params)
        if not q.is_valid():
            return error_response(q.errors, 400)
        data = q.validated_data
        try:
            body = search_posts(
                keyword=data["keyword"],
                type=data.get("type"),
                page=data["page"],
                size=data["size"],
                user=request.user,
            )
        except serializers.ValidationError as exc:
            return error_response(exc.detail, 400)

        response_serializer = PostSearchResponseSerializer(instance=body)
        return Response(response_serializer.data, status=200)


class MyPostsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=[TAG_POSTS],
        summary="나의 포스트 목록 조회",
        description="로그인한 사용자의 게시글 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(
                name="sort_by",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="LATEST (기본값) 또는 POPULAR",
                default="LATEST",
            ),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY, required=False, default=0),
            OpenApiParameter(name="size", type=int, location=OpenApiParameter.QUERY, required=False, default=8),
        ],
        responses={200: PostFeedResponseSerializer},
        examples=[
            OpenApiExample(
                "200 OK",
                value={
                    "posts": [
                        {
                            "post_id": 301,
                            "images": [
                                "https://cdn.example.com/posts/301-1.jpg",
                                "https://cdn.example.com/posts/301-2.jpg",
                            ],
                            "profile_image_url": "https://cdn.example.com/profiles/user-10.jpg",
                            "nickname": "유저",
                            "created_at": "2026-04-08T00:00:00Z",
                            "title": "오늘도 운동 완료!",
                            "tags": ["운동", "러닝"],
                            "content_preview": "오늘은 5km 러닝하고 왔어요.",
                            "like_count": 15,
                            "comment_count": 4,
                            "is_scrapped": True,
                        }
                    ],
                    "page": 0,
                    "size": 8,
                    "total_count": 150,
                },
                response_only=True,
            )
        ],
    )
    def get(self, request: Request) -> Response:
        q = PostListQuerySerializer(data=request.query_params)
        if not q.is_valid():
            return error_response(q.errors, 400)
        data = q.validated_data

        if not request.user.is_authenticated:
            return error_response(
                {"Authorization": ["나의 게시물을 조회하려면 로그인이 필요합니다."]}, status.HTTP_401_UNAUTHORIZED
            )

        try:
            body = list_posts(
                scope=SCOPE_MY,
                sort_by=data["sort_by"],
                page=data["page"],
                size=data["size"],
                user=request.user,
            )
        except serializers.ValidationError as exc:
            return error_response(exc.detail, 400)

        response_serializer = PostFeedResponseSerializer(instance=body)
        return Response(response_serializer.data, 200)
