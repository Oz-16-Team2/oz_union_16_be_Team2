from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.posts.models import Post

class PostAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):

        cls.user = User.objects.create_user(username="testuser", password="password", nickname="tester")
        cls.post = Post.objects.create(
            user=cls.user,
            title="테스트 게시글",
            content="테스트 게시글 내용입니다."
        )

    def setUp(self):

        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("posts-list")
        self.detail_url = reverse("post-detail", kwargs={"post_id": self.post.pk})

    def test_post_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.post.title)

    def test_post_create(self):
        data = {"title": "새 게시글", "content": "새 게시글 내용"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_update(self):
        data = {"title": "수정된 제목", "content": "수정된 내용"}
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "수정된 제목")

    def test_post_delete(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
