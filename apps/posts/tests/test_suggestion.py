"""
추천 알고리즘 Whitebox 테스트.

전략:
- Factory Boy + Faker: 통제된 합성 데이터 생성
- Freezegun: 시스템 시계를 고정하여 time_decay 공식을 결정론적으로 검증
- Method A (Update 우회): 생성 후 UPDATE 쿼리로 created_at 강제 변경
"""

from __future__ import annotations

import datetime

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.posts.models import Post
from apps.posts.services.post_suggestion_service import (
    _AUTHORED_WEIGHT,
    _LIKED_WEIGHT,
    _MAX_DAYS,
    _time_decay,
    get_recommended_posts,
)
from apps.posts.tests.factories import (
    PostFactory_create,
    PostLikeFactory_create,
    PostTagFactory_create,
    TagFactory_create,
    UserFactory_create,
)

# ============================================================
# 1. _time_decay 수학 공식 정확도 검증 (순수 함수, DB 불필요)
# ============================================================


class TestTimeDecayFormula:
    """_time_decay(age_days, max_days) 공식의 수학적 정확도."""

    def test_day_zero_is_full_weight(self) -> None:
        assert _time_decay(0.0, 30.0) == 1.0

    def test_half_life_returns_half_weight(self) -> None:
        assert _time_decay(15.0, 30.0) == pytest.approx(0.5)

    def test_near_expiry_returns_tenth(self) -> None:
        # 27일 경과, max_days=30 → 1 - 27/30 = 0.1
        assert _time_decay(27.0, 30.0) == pytest.approx(0.1, abs=1e-9)

    def test_floor_applied_at_max_days(self) -> None:
        # 30일 = 한계치 → max(0.1, 0.0) = 0.1
        assert _time_decay(30.0, 30.0) == pytest.approx(0.1)

    def test_floor_applied_beyond_max_days(self) -> None:
        # 100일이 지나도 음수가 되지 않고 0.1 유지
        assert _time_decay(100.0, 30.0) == pytest.approx(0.1)

    def test_never_returns_negative(self) -> None:
        assert _time_decay(999.0, 1.0) >= 0.0

    def test_proportional_over_service_max_days(self) -> None:
        # 서비스 상수 _MAX_DAYS를 기준으로 중간 시점이 선형적으로 작동하는지 확인
        for days in [1.0, 5.0, 10.0, 15.0]:
            expected = max(0.1, 1.0 - days / _MAX_DAYS)
            assert _time_decay(days, _MAX_DAYS) == pytest.approx(expected)


# ============================================================
# 2. 시계 고정 통합 테스트 (Freezegun + Factory Boy + Method A)
# ============================================================


@pytest.mark.django_db
class TestTimeDecayWithFrozenClock:
    """Freezegun으로 시계를 고정하여 time_decay가 추천 순위에 미치는 영향 결정론적 검증."""

    @freeze_time("2026-03-15 12:00:00")
    def test_newer_post_ranks_above_older_post_same_tag(self) -> None:
        """
        같은 태그라도 최신 게시글이 오래된 게시글보다 높은 순위를 받아야 한다.

        Method A: create → UPDATE 쿼리로 created_at을 과거로 강제 설정.
        """
        tag = TagFactory_create(name="공부/성장")
        requester = UserFactory_create()
        creator = UserFactory_create()

        # 관심 신호: requester가 해당 태그 게시글에 좋아요
        interest_source = PostFactory_create(user=creator)
        PostTagFactory_create(post=interest_source, tag=tag)
        PostLikeFactory_create(user=requester, post=interest_source)

        # 신규 게시글 (현재 시각 = 2026-03-15, decay ≈ 1.0)
        new_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=new_post, tag=tag)

        # Method A: 오래된 게시글 (15일 전, decay = 1 - 15/20 = 0.25)
        old_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=old_post, tag=tag)
        Post.objects.filter(pk=old_post.pk).update(created_at=timezone.now() - datetime.timedelta(days=15))

        posts, _ = get_recommended_posts(requester, page=1, size=10)
        post_ids = [p.pk for p in posts]

        assert new_post.pk in post_ids
        assert old_post.pk in post_ids
        assert post_ids.index(new_post.pk) < post_ids.index(old_post.pk), (
            "신규 게시글이 오래된 게시글보다 높은 순위여야 합니다"
        )

    @freeze_time("2026-03-15 12:00:00")
    def test_authored_weight_beats_liked_weight_same_age(self) -> None:
        """
        나이가 같을 때 authored(5.0) > liked(3.0) 가중치 순서가 유지되어야 한다.
        """
        authored_tag = TagFactory_create(name="직접작성태그")
        liked_tag = TagFactory_create(name="좋아요태그")
        requester = UserFactory_create()
        creator = UserFactory_create()

        # 관심 신호 A: requester가 authored_tag 게시글 직접 작성 → weight 5.0
        my_authored = PostFactory_create(user=requester)
        PostTagFactory_create(post=my_authored, tag=authored_tag)

        # 관심 신호 B: requester가 liked_tag 게시글에 좋아요 → weight 3.0
        liked_source = PostFactory_create(user=creator)
        PostTagFactory_create(post=liked_source, tag=liked_tag)
        PostLikeFactory_create(user=requester, post=liked_source)

        # 추천 후보: 동일 나이, 태그만 다른 게시글 2개
        authored_tag_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=authored_tag_post, tag=authored_tag)

        liked_tag_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=liked_tag_post, tag=liked_tag)

        posts, _ = get_recommended_posts(requester, page=1, size=10)
        post_ids = [p.pk for p in posts]

        assert authored_tag_post.pk in post_ids
        assert liked_tag_post.pk in post_ids
        assert post_ids.index(authored_tag_post.pk) < post_ids.index(liked_tag_post.pk), (
            f"authored_weight({_AUTHORED_WEIGHT}) > liked_weight({_LIKED_WEIGHT})이므로 "
            "직접 작성 태그 게시글이 먼저 추천되어야 합니다"
        )

    @freeze_time("2026-03-15 12:00:00")
    def test_very_old_post_gets_floor_score_not_excluded(self) -> None:
        """
        _MAX_DAYS를 훨씬 초과한 게시글도 floor(0.1) 덕분에 추천 후보에서 완전 제거되지 않는다.
        """
        tag = TagFactory_create(name="오래된태그")
        requester = UserFactory_create()
        creator = UserFactory_create()

        # 관심 신호
        source = PostFactory_create(user=creator)
        PostTagFactory_create(post=source, tag=tag)
        PostLikeFactory_create(user=requester, post=source)

        # Method A: 1년 전 게시글 (decay = max(0.1, 1 - 365/20) = 0.1)
        ancient_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=ancient_post, tag=tag)
        Post.objects.filter(pk=ancient_post.pk).update(created_at=timezone.now() - datetime.timedelta(days=365))

        posts, _ = get_recommended_posts(requester, page=1, size=100)
        assert any(p.pk == ancient_post.pk for p in posts), (
            "floor 점수(0.1) 덕분에 1년 전 게시글도 후보에 포함되어야 합니다"
        )

    @freeze_time("2026-03-15 12:00:00")
    def test_recent_post_preferred_over_ancient_post(self) -> None:
        """
        신규 게시글(decay≈1.0)이 1년 전 게시글(decay=0.1)보다 앞에 위치해야 한다.
        """
        tag = TagFactory_create(name="혼합태그")
        requester = UserFactory_create()
        creator = UserFactory_create()

        source = PostFactory_create(user=creator)
        PostTagFactory_create(post=source, tag=tag)
        PostLikeFactory_create(user=requester, post=source)

        # Method A: 1년 전 게시글
        ancient_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=ancient_post, tag=tag)
        Post.objects.filter(pk=ancient_post.pk).update(created_at=timezone.now() - datetime.timedelta(days=365))

        # 신규 게시글
        new_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=new_post, tag=tag)

        posts, _ = get_recommended_posts(requester, page=1, size=100)
        post_ids = [p.pk for p in posts]

        assert post_ids.index(new_post.pk) < post_ids.index(ancient_post.pk)


# ============================================================
# 3. 핵심 알고리즘 및 엣지 케이스 검증
# ============================================================


@pytest.mark.django_db
class TestRecommendationCoreLogic:
    """CBF 알고리즘 동작 정확도 및 엣지 케이스."""

    def test_cbf_authored_post_triggers_tag_recommendation(self) -> None:
        """내가 공부 태그 게시글을 쓰면 공부 태그 게시글이 추천된다 (CBF)."""
        tag = TagFactory_create(name="공부_CBF")
        requester = UserFactory_create()
        creator = UserFactory_create()

        my_post = PostFactory_create(user=requester)
        PostTagFactory_create(post=my_post, tag=tag)

        for _ in range(10):
            p = PostFactory_create(user=creator)
            PostTagFactory_create(post=p, tag=tag)

        posts, total = get_recommended_posts(requester, page=1, size=8)

        assert len(posts) == 8
        for p in posts:
            assert p.post_tags.filter(tag=tag).exists(), "CBF 추천이므로 모든 추천 게시글에 관심 태그가 있어야 합니다"

    def test_own_posts_excluded_from_recommendations(self) -> None:
        """내가 작성한 게시글은 추천 목록에 포함되지 않아야 한다."""
        tag = TagFactory_create(name="운동_제외")
        requester = UserFactory_create()
        creator = UserFactory_create()

        my_post = PostFactory_create(user=requester)
        PostTagFactory_create(post=my_post, tag=tag)

        for _ in range(5):
            p = PostFactory_create(user=creator)
            PostTagFactory_create(post=p, tag=tag)

        posts, _ = get_recommended_posts(requester, page=1, size=10)
        assert all(p.user_id != requester.pk for p in posts), "내 게시글이 추천 목록에 포함되었습니다"

    def test_cold_start_returns_latest_posts_as_fallback(self) -> None:
        """활동 내역이 전혀 없는 신규 유저는 최신 게시글 Fallback을 받는다."""
        new_user = UserFactory_create()
        creator = UserFactory_create()

        for _ in range(12):
            PostFactory_create(user=creator)

        posts, total = get_recommended_posts(new_user, page=1, size=8)

        assert len(posts) == 8, "Cold Start 시 8개 Fallback 게시글이 제공되어야 합니다"
        assert total >= 8

    def test_cold_start_ordered_by_recency(self) -> None:
        """Cold Start Fallback은 최신순 정렬이어야 한다."""
        new_user = UserFactory_create()
        creator = UserFactory_create()

        for _ in range(10):
            PostFactory_create(user=creator)

        posts, _ = get_recommended_posts(new_user, page=1, size=10)
        created_ats = [p.created_at for p in posts]
        assert created_ats == sorted(created_ats, reverse=True), "Cold Start Fallback은 최신순 정렬이어야 합니다"

    def test_pagination_returns_disjoint_pages(self) -> None:
        """페이지 1과 페이지 2는 중복 없이 서로 다른 게시글을 반환한다."""
        tag = TagFactory_create(name="여행_페이지")
        requester = UserFactory_create()
        creator = UserFactory_create()

        my_post = PostFactory_create(user=requester)
        PostTagFactory_create(post=my_post, tag=tag)

        for _ in range(20):
            p = PostFactory_create(user=creator)
            PostTagFactory_create(post=p, tag=tag)

        page1, _ = get_recommended_posts(requester, page=1, size=8)
        page2, _ = get_recommended_posts(requester, page=2, size=8)

        ids1 = {p.pk for p in page1}
        ids2 = {p.pk for p in page2}
        assert ids1.isdisjoint(ids2), "두 페이지 간 중복 게시글이 존재합니다"

    def test_multi_tag_post_scores_higher_than_single_tag(self) -> None:
        """
        사용자 관심 태그 2개를 모두 가진 게시글은 태그 1개짜리보다 높은 점수를 받는다.
        """
        tag_a = TagFactory_create(name="멀티A")
        tag_b = TagFactory_create(name="멀티B")
        requester = UserFactory_create()
        creator = UserFactory_create()

        # 관심 신호: 두 태그 모두 authored
        PostTagFactory_create(post=PostFactory_create(user=requester), tag=tag_a)
        PostTagFactory_create(post=PostFactory_create(user=requester), tag=tag_b)

        double_tag_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=double_tag_post, tag=tag_a)
        PostTagFactory_create(post=double_tag_post, tag=tag_b)

        single_tag_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=single_tag_post, tag=tag_a)

        posts, _ = get_recommended_posts(requester, page=1, size=10)
        post_ids = [p.pk for p in posts]

        assert double_tag_post.pk in post_ids
        assert single_tag_post.pk in post_ids
        assert post_ids.index(double_tag_post.pk) < post_ids.index(single_tag_post.pk), (
            "멀티 태그 게시글이 단일 태그 게시글보다 높은 순위여야 합니다"
        )
