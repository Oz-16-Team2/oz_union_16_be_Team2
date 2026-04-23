"""
가상 페르소나를 통한 '시간 압축' 시뮬레이션 (Behavioral Testing).

두 가지 시간 조작 기법:
  Method A (Update 우회): 게시글 생성 → UPDATE 쿼리로 created_at을 과거로 설정
  Method B (Bulk Create + freeze_time): freeze_time으로 시계를 고정한 뒤 bulk_create

두 기법 모두 mypy strict 호환으로 작성.
"""

from __future__ import annotations

import datetime
import random

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.posts.models import Post, PostLike, PostTag, Tag
from apps.posts.services.post_suggestion_service import get_recommended_posts
from apps.posts.tests.factories import (
    PostFactory_create,
    PostLikeFactory_create,
    PostTagFactory_create,
    TagFactory_create,
    UserFactory_create,
)
from apps.posts.tests.suggestion.personas import (
    ALL_PERSONAS,
    HEALTH_ENTHUSIAST,
    MIRACLE_MORNING_USER,
    BotPersona,
)
from apps.users.models import User

# ============================================================
# Method A: Update 우회 기법
# ============================================================


@pytest.mark.django_db
class TestMethodA_UpdateBypass:
    """
    Method A: Post.objects.create() 후 UPDATE 쿼리로 auto_now_add 우회.

    장점: 모델 단건 생성 로직 그대로 사용 가능.
    단점: N+1 쿼리 발생 (생성 + 업데이트 각 1회).
    """

    def test_update_sets_past_created_at(self) -> None:
        """UPDATE 쿼리 후 DB에서 재조회 시 과거 시각이 실제로 반영되는지 확인."""
        creator = UserFactory_create()
        post = PostFactory_create(user=creator)
        target_time = timezone.now() - datetime.timedelta(days=30)

        Post.objects.filter(pk=post.pk).update(created_at=target_time)
        post.refresh_from_db()

        diff = abs((post.created_at - target_time).total_seconds())
        assert diff < 1, "UPDATE 후 created_at이 목표 과거 시각과 일치해야 합니다"

    @freeze_time("2026-03-15 12:00:00")
    def test_time_compressed_scenario_health_persona(self) -> None:
        """
        건강/운동 페르소나 시뮬레이션 (Method A).

        시나리오:
          - 건강봇들이 90일에 걸쳐 건강 태그 게시글을 작성 (과거로 시간 압축)
          - 실제 유저가 건강 태그 게시글에 좋아요 → 건강 태그 게시글 추천 확인
        """
        health_tag = TagFactory_create(name="건강/운동_A")
        real_user = UserFactory_create()

        bot_posts: list[Post] = []
        for _ in range(20):
            bot = UserFactory_create()
            post = PostFactory_create(user=bot)
            PostTagFactory_create(post=post, tag=health_tag)

            days_ago = random.randint(0, 90)
            Post.objects.filter(pk=post.pk).update(created_at=timezone.now() - datetime.timedelta(days=days_ago))
            bot_posts.append(post)

        PostLikeFactory_create(user=real_user, post=bot_posts[0])

        posts, total = get_recommended_posts(real_user, page=1, size=8)

        assert len(posts) > 0, "건강 태그 관심 후 추천 결과가 비어있습니다"
        recommended_tags = {pt.tag.name for p in posts for pt in p.post_tags.all()}
        assert "건강/운동_A" in recommended_tags, "관심 태그(건강/운동)가 추천 결과에 포함되어야 합니다"

    @freeze_time("2026-03-15 12:00:00")
    def test_recent_activity_outscores_old_activity_method_a(self) -> None:
        """
        Method A로 시간 압축:
          오래된 게시글(15일 전)보다 신규 게시글이 더 높은 순위를 받아야 한다.
        """
        tag = TagFactory_create(name="시간압축_A")
        requester = UserFactory_create()
        creator = UserFactory_create()

        source = PostFactory_create(user=creator)
        PostTagFactory_create(post=source, tag=tag)
        PostLikeFactory_create(user=requester, post=source)

        old_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=old_post, tag=tag)
        Post.objects.filter(pk=old_post.pk).update(created_at=timezone.now() - datetime.timedelta(days=15))

        new_post = PostFactory_create(user=creator)
        PostTagFactory_create(post=new_post, tag=tag)

        posts, _ = get_recommended_posts(requester, page=1, size=10)
        post_ids = [p.pk for p in posts]

        assert post_ids.index(new_post.pk) < post_ids.index(old_post.pk), (
            "신규 게시글이 오래된 게시글보다 높은 순위여야 합니다 (Method A)"
        )


# ============================================================
# Method B: Bulk Create + freeze_time 기법
# ============================================================


@pytest.mark.django_db
class TestMethodB_BulkCreate:
    """
    Method B: bulk_create + freeze_time 조합으로 과거 시간 일괄 삽입.

    Django 6.0에서 bulk_create는 auto_now_add 필드에 pre_save()를 호출하므로
    인스턴스에 직접 created_at을 지정하는 것만으로는 우회가 불가능하다.
    대신 freeze_time으로 시스템 시계를 원하는 과거 시각으로 고정한 뒤 bulk_create를 실행하면
    auto_now_add가 그 고정된 시각을 캡처한다.

    장점: 단 1회 INSERT + 코드 간결 (각 게시글에 UPDATE 불필요).
    사용처: 특정 날짜에 다량의 데이터가 생성된 상황을 재현할 때.
    """

    def test_bulk_create_with_frozen_time_sets_past_created_at(self) -> None:
        """
        freeze_time으로 시계를 2026-01-15로 고정한 뒤 bulk_create하면
        auto_now_add가 그 고정 시각을 캡처한다.
        """
        creator = UserFactory_create()
        target_date = "2026-01-15 09:00:00"

        with freeze_time(target_date):
            frozen_now = timezone.now()
            instances = [Post(user=creator, title=f"과거글 {i}", content="bulk_create 테스트") for i in range(5)]
            created = Post.objects.bulk_create(instances)

        for post in created:
            post.refresh_from_db()
            diff = abs((post.created_at - frozen_now).total_seconds())
            assert diff < 1, (
                f"freeze_time + bulk_create 후 created_at({post.created_at})이 "
                f"고정 시각({frozen_now})과 일치해야 합니다"
            )

    @freeze_time("2026-03-15 12:00:00")
    def test_time_compressed_bulk_scenario(self) -> None:
        """
        Method B로 90일치 게시글 이력을 단 1개 INSERT로 시뮬레이션.
        """
        health_tag = TagFactory_create(name="건강/운동_B")
        miracle_tag = TagFactory_create(name="공부/성장_B")
        real_user = UserFactory_create()
        bot_user = UserFactory_create()
        now = timezone.now()

        health_instances = [
            Post(
                user=bot_user,
                title=f"헬스장 {i}일차",
                content="오늘도 오운완",
                created_at=now - datetime.timedelta(days=random.randint(0, 90)),
            )
            for i in range(15)
        ]
        health_posts = Post.objects.bulk_create(health_instances)
        PostTag.objects.bulk_create([PostTag(post=p, tag=health_tag) for p in health_posts])

        study_instances = [
            Post(
                user=bot_user,
                title=f"파이썬 {i}일차",
                content="알고리즘 공부",
                created_at=now - datetime.timedelta(days=random.randint(0, 30)),
            )
            for i in range(10)
        ]
        study_posts = Post.objects.bulk_create(study_instances)
        PostTag.objects.bulk_create([PostTag(post=p, tag=miracle_tag) for p in study_posts])

        PostLike.objects.create(user=real_user, post=health_posts[0])

        posts, _ = get_recommended_posts(real_user, page=1, size=8)

        assert len(posts) > 0, "추천 결과가 비어있습니다"
        recommended_tags = {pt.tag.name for p in posts for pt in p.post_tags.all()}
        assert "건강/운동_B" in recommended_tags

    @freeze_time("2026-03-15 12:00:00")
    def test_bulk_created_posts_ranked_by_recency(self) -> None:
        """
        Method B로 다양한 과거 시각에 삽입한 게시글이 최신순으로 정렬되어 추천되는지 확인.
        """
        tag = TagFactory_create(name="시간압축_B")
        requester = UserFactory_create()
        creator = UserFactory_create()
        now = timezone.now()

        source = PostFactory_create(user=creator)
        PostTagFactory_create(post=source, tag=tag)
        PostLikeFactory_create(user=requester, post=source)

        day_offsets = [5, 10, 15, 20]
        instances = [
            Post(
                user=creator,
                title=f"{d}일 전 게시글",
                content="내용",
                created_at=now - datetime.timedelta(days=d),
            )
            for d in day_offsets
        ]
        bulk_posts = Post.objects.bulk_create(instances)
        PostTag.objects.bulk_create([PostTag(post=p, tag=tag) for p in bulk_posts])

        posts, _ = get_recommended_posts(requester, page=1, size=10)

        post_titles = [p.title for p in posts if p.title.endswith("일 전 게시글")]
        days_in_result = [int(t.split("일")[0]) for t in post_titles]
        assert days_in_result == sorted(days_in_result), (
            "최신 게시글(5일)부터 오래된 게시글(20일) 순으로 정렬되어야 합니다"
        )


# ============================================================
# 페르소나 시뮬레이션 (Method A + B 혼합)
# ============================================================


def _create_persona_posts(persona: BotPersona, tag_map: dict[str, Tag]) -> tuple[list[User], list[Post]]:
    """Method B (bulk_create)로 페르소나 봇의 게시글을 시간 압축하여 생성."""
    now = timezone.now()
    bots: list[User] = []
    post_instances: list[Post] = []
    post_tag_pairs: list[tuple[int, Tag]] = []

    all_tags = list(tag_map.values())
    use_all_tags = persona.preferred_tags == ["all"]
    preferred = all_tags if use_all_tags else [tag_map[n] for n in persona.preferred_tags if n in tag_map]

    for i in range(persona.count):
        user, _ = User.objects.get_or_create(
            email=f"{persona.prefix}_{i}@test.com",
            defaults={"nickname": f"{persona.prefix}_{i}"},
        )
        bots.append(user)

        num_posts = random.randint(*persona.posts_range)
        active_days = random.randint(*persona.active_days_range)

        for _ in range(num_posts):
            days_ago = random.randint(0, active_days)
            hour = random.choice(persona.posting_hours)
            created_at = now - datetime.timedelta(days=days_ago, hours=hour)

            idx = len(post_instances)
            post_instances.append(
                Post(
                    user=user,
                    title=random.choice(persona.title_pool),
                    content=random.choice(persona.content_pool),
                    created_at=created_at,
                )
            )

            num_tags = random.randint(*persona.tags_per_post)
            if num_tags > 0 and preferred:
                for tag in random.sample(preferred, min(num_tags, len(preferred))):
                    post_tag_pairs.append((idx, tag))

    created_posts = Post.objects.bulk_create(post_instances)

    if post_tag_pairs:
        PostTag.objects.bulk_create(
            [PostTag(post=created_posts[idx], tag=tag) for idx, tag in post_tag_pairs],
            ignore_conflicts=True,
        )

    return bots, created_posts


@pytest.mark.django_db
class TestPersonaSimulation:
    """완전한 페르소나 시뮬레이션: Method A + B 혼합하여 시간 압축 검증."""

    @pytest.fixture(autouse=True)
    def setup_tags(self) -> dict[str, Tag]:
        # 페르소나 정의의 preferred_tags와 정확히 일치해야 함 (공백 포함)
        tags: dict[str, Tag] = {
            "건강 / 운동": Tag.objects.get_or_create(name="건강 / 운동")[0],
            "공부 / 성장": Tag.objects.get_or_create(name="공부 / 성장")[0],
            "습관 / 라이프스타일": Tag.objects.get_or_create(name="습관 / 라이프스타일")[0],
            "일 / 효율": Tag.objects.get_or_create(name="일 / 효율")[0],
            "마음관리 / 절제": Tag.objects.get_or_create(name="마음관리 / 절제")[0],
            "개발 / 코딩": Tag.objects.get_or_create(name="개발 / 코딩")[0],
        }
        self.tag_map = tags
        return tags

    @freeze_time("2026-03-15 12:00:00")
    def test_health_enthusiast_gets_health_content(self) -> None:
        """
        건강 페르소나 봇들이 90일치 게시글 작성 후,
        건강 콘텐츠에 관심 있는 실제 유저에게 건강 태그 게시글이 추천된다.
        """
        health_persona = HEALTH_ENTHUSIAST
        _create_persona_posts(health_persona, self.tag_map)

        real_user = UserFactory_create()
        health_bots = User.objects.filter(email__startswith=f"{health_persona.prefix}_")
        health_posts = Post.objects.filter(user__in=health_bots, post_tags__tag__name="건강 / 운동").distinct()

        first_health_post = health_posts.first()
        if first_health_post is not None:
            PostLike.objects.create(user=real_user, post=first_health_post)

        posts, _ = get_recommended_posts(real_user, page=1, size=8)

        assert len(posts) > 0, "건강 페르소나 시뮬레이션 후 추천 결과가 없습니다"
        all_tags_in_result = {pt.tag.name for p in posts for pt in p.post_tags.all()}
        assert "건강 / 운동" in all_tags_in_result, "건강 관심 유저에게 건강 태그 게시글이 추천되어야 합니다"

    @freeze_time("2026-03-15 12:00:00")
    def test_miracle_morning_user_gets_growth_content(self) -> None:
        """공부/성장 페르소나 봇 시뮬레이션 후 실제 유저에게 성장 관련 콘텐츠가 추천된다."""
        _create_persona_posts(MIRACLE_MORNING_USER, self.tag_map)

        real_user = UserFactory_create()
        miracle_bots = User.objects.filter(email__startswith=f"{MIRACLE_MORNING_USER.prefix}_")
        study_posts = Post.objects.filter(user__in=miracle_bots, post_tags__tag__name="공부 / 성장").distinct()

        first_study_post = study_posts.first()
        if first_study_post is not None:
            PostLike.objects.create(user=real_user, post=first_study_post)

        posts, _ = get_recommended_posts(real_user, page=1, size=8)
        assert len(posts) > 0

    @freeze_time("2026-03-15 12:00:00")
    def test_cold_start_persona_gets_fallback(self) -> None:
        """신규 유저(활동 없음)는 페르소나 데이터가 존재해도 Fallback(최신순)을 받는다."""
        _create_persona_posts(HEALTH_ENTHUSIAST, self.tag_map)

        cold_user = UserFactory_create()
        posts, total = get_recommended_posts(cold_user, page=1, size=8)

        assert len(posts) == 8, "Cold Start 유저에게 8개 Fallback 게시글이 제공되어야 합니다"
        created_ats = [p.created_at for p in posts]
        assert created_ats == sorted(created_ats, reverse=True), "Cold Start Fallback은 최신순 정렬이어야 합니다"

    @freeze_time("2026-03-15 12:00:00")
    def test_time_decay_across_all_personas(self) -> None:
        """
        모든 페르소나가 생성한 게시글 중 최신 게시글이 오래된 게시글보다 상위에 위치하는지 확인.
        (Method B: bulk_create로 모든 페르소나 데이터 일괄 삽입)
        """
        for persona in ALL_PERSONAS:
            _create_persona_posts(persona, self.tag_map)

        real_user = UserFactory_create()
        creator = UserFactory_create()

        for tag_name in ("건강 / 운동", "공부 / 성장"):
            if tag_name in self.tag_map:
                source = PostFactory_create(user=creator)
                PostTagFactory_create(post=source, tag=self.tag_map[tag_name])
                PostLikeFactory_create(user=real_user, post=source)

        posts, _ = get_recommended_posts(real_user, page=1, size=20)
        assert len(posts) > 0
