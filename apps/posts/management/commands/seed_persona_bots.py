from __future__ import annotations

import random
from argparse import ArgumentParser
from datetime import timedelta
from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.posts.models import Post, PostTag, Tag
from apps.posts.tests.suggestion.bot_factory import BotFactory
from apps.posts.tests.suggestion.scenarios import (
    BASIC_RECOMMENDATION_TEST,
    COLD_START_TEST,
    TREND_DETECTION_TEST,
)
from apps.users.models import User

SCENARIOS = {
    "basic": BASIC_RECOMMENDATION_TEST,
    "cold_start": COLD_START_TEST,
    "trend": TREND_DETECTION_TEST,
}

# trend 시나리오에서 스파이크 게시글을 작성할 봇 계정 식별자
_SPIKE_BOT_EMAIL = "spike_bot@seed.com"
_SPIKE_BOT_NICKNAME = "spike_bot"


class Command(BaseCommand):
    help = "페르소나 봇 및 테스트 데이터 생성"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--scenario",
            type=str,
            default="basic",
            choices=list(SCENARIOS.keys()),
            help="테스트 시나리오 선택 (기본값: basic)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="사용 가능한 시나리오 목록 출력",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options["list"]:
            self.stdout.write("사용 가능한 시나리오:")
            for key, scenario in SCENARIOS.items():
                bot_names = ", ".join(p.prefix for p in scenario.personas)
                self.stdout.write(f"  {key}: {scenario.description}")
                self.stdout.write(f"        생성 봇: {bot_names}")
            return

        scenario = SCENARIOS[options["scenario"]]
        self.stdout.write(f"\n시나리오: {scenario.name} — {scenario.description}")

        all_tags = list(Tag.objects.filter(is_active=True))
        if not all_tags:
            raise CommandError("태그가 없습니다. 먼저 seed_tag 커맨드를 실행하세요.")

        # ── 페르소나별 봇 생성 ──────────────────────────────────────
        for persona in scenario.personas:
            try:
                factory = BotFactory(persona, all_tags)
                bots, posts = factory.create_bots_with_posts()
                self.stdout.write(
                    self.style.SUCCESS(f"  [{persona.prefix}] 유저 {len(bots)}명, 포스트 {len(posts)}개 생성")
                )
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f"  [{persona.prefix}] 건너뜀 — {e}"))

        # ── 트렌드 스파이크 생성 (extra_config에 spike_tag가 있을 때만) ──
        cfg = scenario.extra_config
        if cfg.get("spike_tag"):
            self._create_trend_spike(
                spike_tag_name=str(cfg["spike_tag"]),
                spike_days=int(cfg.get("spike_days", 3)),
                spike_multiplier=int(cfg.get("spike_multiplier", 5)),
            )

        self.stdout.write(self.style.SUCCESS("\n완료!"))

    def _create_trend_spike(
        self,
        spike_tag_name: str,
        spike_days: int,
        spike_multiplier: int,
    ) -> None:
        """
        특정 태그가 최근 spike_days일간 급증하는 상황을 재현.
        spike_multiplier배 분량의 게시글을 spike_days 이내의 과거 시각으로 삽입.
        """
        tag = Tag.objects.filter(name=spike_tag_name, is_active=True).first()
        if tag is None:
            self.stdout.write(
                self.style.WARNING(f"  [spike] 태그 '{spike_tag_name}'를 찾을 수 없어 스파이크를 건너뜁니다.")
            )
            return

        spike_bot, _ = User.objects.get_or_create(
            email=_SPIKE_BOT_EMAIL,
            defaults={"nickname": _SPIKE_BOT_NICKNAME, "password": make_password("dummy_hash!")},
        )

        now = timezone.now()
        spike_count = 10 * spike_multiplier  # 기준 10개 × 배수

        post_instances = [
            Post(
                user=spike_bot,
                title=f"[트렌드] {spike_tag_name} 급상승 {i}",
                content="최근 인기 급상승 콘텐츠입니다.",
                # Method A용 placeholder — 생성 후 UPDATE로 과거 시각 설정
            )
            for i in range(spike_count)
        ]
        created = Post.objects.bulk_create(post_instances)

        # Method A: UPDATE 쿼리로 spike_days 이내 과거 시각 강제 삽입
        for post in created:
            past = now - timedelta(
                days=random.randint(0, spike_days - 1),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            Post.objects.filter(pk=post.pk).update(created_at=past)

        PostTag.objects.bulk_create(
            [PostTag(post=p, tag=tag) for p in created],
            ignore_conflicts=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"  [spike] '{spike_tag_name}' 태그 게시글 {spike_count}개를 최근 {spike_days}일 안에 삽입"
            )
        )
