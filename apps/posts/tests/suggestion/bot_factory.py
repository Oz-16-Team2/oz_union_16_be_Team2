"""
봇 생성 팩토리.

Method B (bulk_create): auto_now_add를 우회하기 위해 Post 인스턴스에 created_at을 직접
지정한 뒤 bulk_create로 일괄 삽입. save()를 호출하지 않으므로 auto_now_add가 무시됨.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.posts.models import Post, PostTag, Tag
from apps.posts.tests.suggestion.personas import BotPersona
from apps.users.models import User


class BotFactory:
    """봇 생성 팩토리"""

    def __init__(self, persona: BotPersona, all_tags: list[Tag]) -> None:
        self.persona = persona
        self.all_tags = all_tags
        self._validate_tags()

    def _validate_tags(self) -> None:
        if self.persona.preferred_tags == ["all"]:
            return
        existing_tag_names = {t.name for t in self.all_tags}
        missing = set(self.persona.preferred_tags) - existing_tag_names
        if missing:
            raise ValueError(f"누락된 태그: {missing}")

    def get_preferred_tags(self) -> list[Tag]:
        if self.persona.preferred_tags == ["all"]:
            return self.all_tags
        return [t for t in self.all_tags if t.name in self.persona.preferred_tags]

    @transaction.atomic
    def create_bots_with_posts(self) -> tuple[list[User], list[Post]]:
        bots = self._create_users()
        posts = self._create_posts_for_bots(bots)
        return bots, posts

    def _create_users(self) -> list[User]:
        users: list[User] = []
        for i in range(self.persona.count):
            user, _ = User.objects.get_or_create(
                email=f"{self.persona.prefix}_{i}@test.com",
                defaults={"nickname": f"{self.persona.prefix}_{i}", "password": "dummy_hash!"},
            )
            users.append(user)
        return users

    def _create_posts_for_bots(self, bots: list[User]) -> list[Post]:
        """
        Method B: bulk_create로 auto_now_add 우회.

        Post 인스턴스에 created_at을 직접 지정한 뒤 bulk_create로 삽입.
        bulk_create는 save()를 호출하지 않으므로 auto_now_add가 실행되지 않아
        지정한 과거 시각이 DB에 그대로 저장됨.
        """
        preferred_tags = self.get_preferred_tags()
        post_instances: list[Post] = []
        # (post 인스턴스 인덱스, 연결할 태그 목록) 매핑 — bulk_create 후 pk 매핑에 사용
        post_tag_plan: list[tuple[int, list[Tag]]] = []

        for bot in bots:
            num_posts = random.randint(*self.persona.posts_range)
            active_days = random.randint(*self.persona.active_days_range)

            for _ in range(num_posts):
                idx = len(post_instances)
                post_instances.append(
                    Post(
                        user=bot,
                        title=random.choice(self.persona.title_pool),
                        content=random.choice(self.persona.content_pool),
                        created_at=self._generate_posting_time(active_days),
                    )
                )

                num_tags = random.randint(*self.persona.tags_per_post)
                if num_tags > 0 and preferred_tags:
                    selected = random.sample(preferred_tags, min(num_tags, len(preferred_tags)))
                    post_tag_plan.append((idx, selected))

        # 단일 INSERT로 모든 게시글 생성 (PostgreSQL은 bulk_create 후 pk 반환 지원)
        created_posts = Post.objects.bulk_create(post_instances)

        post_tag_bulk: list[PostTag] = [
            PostTag(post=created_posts[idx], tag=tag) for idx, tags in post_tag_plan for tag in tags
        ]
        if post_tag_bulk:
            PostTag.objects.bulk_create(post_tag_bulk, ignore_conflicts=True)

        return created_posts

    def _generate_posting_time(self, active_days: int) -> datetime:
        """페르소나의 활동 시간 패턴을 반영한 과거 시각 생성."""
        days_ago = random.randint(0, active_days)
        hour = random.choice(self.persona.posting_hours)
        minute = random.randint(0, 59)
        return timezone.now() - timedelta(days=days_ago, hours=hour, minutes=minute)
