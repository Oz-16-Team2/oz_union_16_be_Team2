from __future__ import annotations

from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.choices import PostStatus
from apps.posts.models import Comment, Post, PostLike, PostTag, Scrap, Tag
from apps.users.models import User
from apps.votes.models import Vote, VoteOption


class AdminPostAPIViewTest(APITestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="test1234",
            nickname="admin_user",
            is_staff=True,
        )
        self.normal_user = User.objects.create_user(
            email="user@test.com",
            password="test1234",
            nickname="normal_user",
            is_staff=False,
        )
        self.author = User.objects.create_user(
            email="author@test.com",
            password="test1234",
            nickname="author_user",
            profile_image_url="https://example.com/characters/char_01.png",
        )
        self.comment_user = User.objects.create_user(
            email="comment@test.com",
            password="test1234",
            nickname="comment_user",
            profile_image_url="https://example.com/characters/char_02.png",
        )

        self.tag1 = Tag.objects.create(name="운동", is_active=True)
        self.tag2 = Tag.objects.create(name="공부", is_active=True)

        self.post_with_vote = Post.objects.create(
            user=self.author,
            title="오늘 목표 성공",
            content="운동 완료했습니다.",
            images=[
                "https://example.com/posts/post_1_img_1.png",
                "https://example.com/posts/post_1_img_2.png",
            ],
            is_private=False,
            goal_title="매일 운동하기",
            goal_progress=70,
            status=PostStatus.REPORTED,
        )
        self.post_without_vote = Post.objects.create(
            user=self.author,
            title="공부 인증합니다",
            content="오늘은 알고리즘 3문제 풀었습니다.",
            images=["https://example.com/posts/post_2_img_1.png"],
            is_private=False,
            status=PostStatus.NORMAL,
        )

        PostTag.objects.create(post=self.post_with_vote, tag=self.tag1)
        PostTag.objects.create(post=self.post_without_vote, tag=self.tag2)

        Comment.objects.create(
            post=self.post_with_vote,
            user=self.comment_user,
            content="응원합니다!",
        )

        PostLike.objects.create(post=self.post_with_vote, user=self.author)
        PostLike.objects.create(post=self.post_with_vote, user=self.comment_user)
        Scrap.objects.create(post=self.post_with_vote, user=self.comment_user)

        self.vote = Vote.objects.create(
            post=self.post_with_vote,
            question="내일도 운동할까요?",
            start_at="2026-04-13T09:00:00Z",
            end_at="2026-04-14T09:00:00Z",
        )
        VoteOption.objects.create(vote=self.vote, content="찬성", sort_order=1)
        VoteOption.objects.create(vote=self.vote, content="반대", sort_order=2)

    def test_admin_can_get_post_list(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(
            "/api/v1/admin/posts",
            {"page": 1, "size": 10},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(len(response.data["detail"]), 2)

    def test_post_list_can_filter_by_has_vote(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(
            "/api/v1/admin/posts",
            {"page": 1, "size": 10, "has_vote": True},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["detail"]), 1)
        self.assertEqual(response.data["detail"][0]["id"], self.post_with_vote.id)

    def test_post_list_can_filter_by_status(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(
            "/api/v1/admin/posts",
            {"page": "1", "size": "10", "status": "REPORTED"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["detail"]), 1)
        self.assertEqual(response.data["detail"][0]["status"], "REPORTED")

    def test_post_list_returns_400_when_query_is_invalid(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(
            "/api/v1/admin/posts",
            {"page": 0, "size": 10},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "잘못된 요청입니다.")

    def test_post_list_returns_401_when_unauthenticated(self) -> None:
        response = self.client.get(
            "/api/v1/admin/posts",
            {"page": 1, "size": 10},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "관리자 인증이 필요합니다.")

    def test_post_list_returns_403_when_not_admin(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(
            "/api/v1/admin/posts",
            {"page": 1, "size": 10},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")

    def test_admin_can_get_post_detail(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(f"/api/v1/admin/posts/{self.post_with_vote.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"]["id"], self.post_with_vote.id)
        self.assertEqual(response.data["detail"]["title"], "오늘 목표 성공")
        self.assertEqual(len(response.data["detail"]["comments"]), 1)
        self.assertIsNotNone(response.data["detail"]["vote"])

    def test_post_detail_returns_404_when_post_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/v1/admin/posts/99999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "게시글을 찾을 수 없습니다.")

    def test_admin_can_delete_post(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(f"/api/v1/admin/posts/{self.post_with_vote.id}/delete")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "게시글이 삭제되었습니다.")

        self.post_with_vote.refresh_from_db()
        self.assertIsNotNone(self.post_with_vote.deleted_at)

    def test_delete_post_returns_404_when_post_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete("/api/v1/admin/posts/99999/delete")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "게시글을 찾을 수 없습니다.")

    def test_admin_can_update_post_status(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            f"/api/v1/admin/posts/{self.post_without_vote.id}/status",
            {"status": "HIDDEN"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "게시글 상태가 수정되었습니다.")

        self.post_without_vote.refresh_from_db()
        self.assertEqual(self.post_without_vote.status, PostStatus.HIDDEN)

    def test_update_post_status_returns_400_when_status_is_invalid(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            f"/api/v1/admin/posts/{self.post_without_vote.id}/status",
            {"status": "WRONG"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "잘못된 요청입니다.")

    def test_update_post_status_returns_404_when_post_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            "/api/v1/admin/posts/99999/status",
            {"status": "HIDDEN"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "게시글을 찾을 수 없습니다.")
