from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.response import detail_response, error_response
from apps.posts.models import Post
from apps.posts.services.post_like_service import PostLikeService


class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, post_id: int) -> Response:
        if not request.user.is_authenticated:
            return error_response({"detail": ["로그인이 필요합니다."]}, 401)

        try:
            is_liked = PostLikeService.toggle_like(post_id=post_id, user=request.user)

            return detail_response({"detail": "게시글 좋아요 처리가 완료되었습니다.", "is_liked": is_liked}, 200)

        except Post.DoesNotExist:
            return error_response({"error_detail": {"postId": ["해당 게시글을 찾을 수 없습니다."]}}, 404)
