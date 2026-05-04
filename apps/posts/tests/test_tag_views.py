import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Scrap, Tag
from apps.posts.tests.factories import (
    PostFactory_create,
    PostTagFactory_create,
    TagFactory_create,
    UserFactory_create,
)
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User


# ==========================================
# 1. 태그 목록/검색 (REQ-TAG-001)
# GET /api/v1/posts/tags
# ==========================================
@pytest.mark.django_db
class TestTagListView:
    URL = "/api/v1/posts/tags"

    @pytest.fixture
    def user(self) -> User:
        return UserFactory_create()

    @pytest.fixture
    def client(self, user: User) -> APIClient:
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    def test_unauthenticated_returns_401(self) -> None:
        response = APIClient().get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_only_active_tags(self, client: APIClient) -> None:
        TagFactory_create(name="활성태그", is_active=True)
        TagFactory_create(name="비활성태그", is_active=False)

        response = client.get(self.URL)

        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data["results"]]
        assert "활성태그" in names
        assert "비활성태그" not in names

    def test_keyword_filters_tags(self, client: APIClient) -> None:
        TagFactory_create(name="운동하기", is_active=True)
        TagFactory_create(name="독서하기", is_active=True)

        response = client.get(self.URL, {"keyword": "운동"})

        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data["results"]]
        assert "운동하기" in names
        assert "독서하기" not in names

    def test_keyword_case_insensitive(self, client: APIClient) -> None:
        TagFactory_create(name="Python", is_active=True)

        response = client.get(self.URL, {"keyword": "python"})

        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data["results"]]
        assert "Python" in names

    def test_keyword_no_match_returns_empty(self, client: APIClient) -> None:
        TagFactory_create(name="운동", is_active=True)

        response = client.get(self.URL, {"keyword": "없는태그xyz"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_no_keyword_returns_all_active_tags(self, client: APIClient) -> None:
        tag1 = TagFactory_create(name="태그A", is_active=True)
        tag2 = TagFactory_create(name="태그B", is_active=True)
        TagFactory_create(name="태그C", is_active=False)

        response = client.get(self.URL)

        assert response.status_code == status.HTTP_200_OK
        ids = [t["id"] for t in response.data["results"]]
        assert tag1.id in ids
        assert tag2.id in ids

    def test_keyword_result_limited_to_20(self, client: APIClient) -> None:
        for i in range(25):
            TagFactory_create(name=f"검색태그{i:02d}", is_active=True)

        response = client.get(self.URL, {"keyword": "검색태그"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) <= 20

    def test_no_keyword_result_limited_to_50(self, client: APIClient) -> None:
        for i in range(55):
            TagFactory_create(name=f"전체태그{i:02d}", is_active=True)

        response = client.get(self.URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) <= 50

    def test_response_contains_expected_fields(self, client: APIClient) -> None:
        TagFactory_create(name="필드확인태그", is_active=True)

        response = client.get(self.URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        tag = response.data["results"][0]
        assert "id" in tag
        assert "name" in tag

    def test_blank_keyword_treated_as_no_keyword(self, client: APIClient) -> None:
        TagFactory_create(name="운동", is_active=True)

        response = client.get(self.URL, {"keyword": "   "})

        assert response.status_code == status.HTTP_200_OK
        names = [t["name"] for t in response.data["results"]]
        assert "운동" in names


# ==========================================
# 2. 태그별 게시글 조회 (REQ-POST-011)
# GET /api/v1/tags/{tag_id}/posts
# ==========================================
@pytest.mark.django_db
class TestTagPostListView:
    @pytest.fixture
    def user(self) -> User:
        return UserFactory_create()

    @pytest.fixture
    def client(self, user: User) -> APIClient:
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    @pytest.fixture
    def active_tag(self) -> Tag:
        return TagFactory_create(name="활성태그", is_active=True)

    @pytest.fixture
    def inactive_tag(self) -> Tag:
        return TagFactory_create(name="비활성태그", is_active=False)

    def url(self, tag_id: int) -> str:
        return f"/api/v1/tags/{tag_id}/posts"

    def test_unauthenticated_returns_401(self, active_tag: Tag) -> None:
        response = APIClient().get(self.url(active_tag.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_tag_not_found_returns_404(self, client: APIClient) -> None:
        response = client.get(self.url(99999))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inactive_tag_returns_404(self, client: APIClient, inactive_tag: Tag) -> None:
        response = client.get(self.url(inactive_tag.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_page_returns_400(self, client: APIClient, active_tag: Tag) -> None:
        response = client.get(self.url(active_tag.id), {"page": 0})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_size_over_max_returns_400(self, client: APIClient, active_tag: Tag) -> None:
        response = client.get(self.url(active_tag.id), {"size": 101})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_tag_returns_empty_posts(self, client: APIClient, active_tag: Tag) -> None:
        response = client.get(self.url(active_tag.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"]["posts"] == []
        assert response.data["detail"]["total_count"] == 0

    def test_returns_posts_with_tag(self, client: APIClient, active_tag: Tag) -> None:
        post = PostFactory_create()
        PostTagFactory_create(post=post, tag=active_tag)

        response = client.get(self.url(active_tag.id))

        assert response.status_code == status.HTTP_200_OK
        post_ids = [p["post_id"] for p in response.data["detail"]["posts"]]
        assert post.id in post_ids

    def test_does_not_return_posts_without_tag(self, client: APIClient, active_tag: Tag) -> None:
        PostFactory_create()  # 해당 태그 없는 게시글

        response = client.get(self.url(active_tag.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"]["posts"] == []

    def test_response_structure(self, client: APIClient, active_tag: Tag) -> None:
        post = PostFactory_create()
        PostTagFactory_create(post=post, tag=active_tag)

        response = client.get(self.url(active_tag.id))

        assert response.status_code == status.HTTP_200_OK
        detail = response.data["detail"]
        assert "posts" in detail
        assert "page" in detail
        assert "size" in detail
        assert "total_count" in detail

    def test_post_item_fields(self, client: APIClient, active_tag: Tag) -> None:
        post = PostFactory_create()
        PostTagFactory_create(post=post, tag=active_tag)

        response = client.get(self.url(active_tag.id))

        item = response.data["detail"]["posts"][0]
        for field in [
            "post_id",
            "images",
            "profile_image_url",
            "nickname",
            "created_at",
            "title",
            "tags",
            "content_preview",
            "like_count",
            "comment_count",
            "is_scrapped",
        ]:
            assert field in item, f"'{field}' 필드가 응답에 없습니다."

    def test_tags_field_includes_all_tags_of_post(self, client: APIClient, active_tag: Tag) -> None:
        other_tag = TagFactory_create(name="다른태그", is_active=True)
        post = PostFactory_create()
        PostTagFactory_create(post=post, tag=active_tag)
        PostTagFactory_create(post=post, tag=other_tag)

        response = client.get(self.url(active_tag.id))

        item = response.data["detail"]["posts"][0]
        assert active_tag.name in item["tags"]
        assert other_tag.name in item["tags"]

    def test_profile_image_url_for_normal_user(self, client: APIClient, active_tag: Tag) -> None:
        post = PostFactory_create()
        PostTagFactory_create(post=post, tag=active_tag)

        response = client.get(self.url(active_tag.id))

        item = response.data["detail"]["posts"][0]
        expected_url = PROFILE_IMAGE_URL_MAP.get(post.user.profile_image)
        assert item["profile_image_url"] == expected_url

    def test_content_preview_truncated_to_100(self, client: APIClient, active_tag: Tag) -> None:
        post = PostFactory_create(content="A" * 200)
        PostTagFactory_create(post=post, tag=active_tag)

        response = client.get(self.url(active_tag.id))

        item = response.data["detail"]["posts"][0]
        assert len(item["content_preview"]) <= 100

    def test_is_scrapped_true_when_user_scrapped(self, client: APIClient, user: User, active_tag: Tag) -> None:
        post = PostFactory_create()
        PostTagFactory_create(post=post, tag=active_tag)
        Scrap.objects.create(user=user, post=post)

        response = client.get(self.url(active_tag.id))

        item = response.data["detail"]["posts"][0]
        assert item["is_scrapped"] is True

    def test_is_scrapped_false_when_user_not_scrapped(self, client: APIClient, active_tag: Tag) -> None:
        post = PostFactory_create()
        PostTagFactory_create(post=post, tag=active_tag)

        response = client.get(self.url(active_tag.id))

        item = response.data["detail"]["posts"][0]
        assert item["is_scrapped"] is False

    def test_pagination_size(self, client: APIClient, active_tag: Tag) -> None:
        for _ in range(10):
            PostTagFactory_create(post=PostFactory_create(), tag=active_tag)

        response = client.get(self.url(active_tag.id), {"page": 1, "size": 3})

        assert response.status_code == status.HTTP_200_OK
        detail = response.data["detail"]
        assert len(detail["posts"]) == 3
        assert detail["total_count"] == 10
        assert detail["page"] == 1
        assert detail["size"] == 3

    def test_pagination_second_page(self, client: APIClient, active_tag: Tag) -> None:
        for _ in range(5):
            PostTagFactory_create(post=PostFactory_create(), tag=active_tag)

        response = client.get(self.url(active_tag.id), {"page": 2, "size": 3})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["detail"]["posts"]) == 2
