"""
engagement_profiles.py 기반으로 봇 간 좋아요를 시뮬레이션합니다.

사전 조건:
  1. python manage.py seed_tag
  2. python manage.py seed_persona_bots --scenario basic (또는 trend)

사용법:
  uv run python manage.py seed_engagement
  uv run python manage.py seed_engagement --dry-run        # 저장 없이 수치만 출력
  uv run python manage.py seed_engagement --reset          # 기존 봇 좋아요 초기화 후 재생성
  uv run python manage.py seed_engagement --scale 0.05     # 좋아요 확률 5% 수준으로 추가 축소
  uv run python manage.py seed_engagement --persona health_bot
"""

from __future__ import annotations

import random
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from apps.posts.models import Post, PostLike, PostTag
from apps.posts.tests.suggestion.engagement_profiles import ENGAGEMENT_PROFILES
from apps.users.models import User

# engagement_rate × like_probability를 이 값으로 추가 스케일 다운.
# 기본 0.1 → health_bot(0.35×0.70=24.5%) × 0.1 ≈ 2.5% 수준으로 조정.
_DEFAULT_SCALE = 0.1


def _get_bot_type(email: str) -> str | None:
    """이메일 prefix에서 봇 타입 추출. 봇이 아니면 None 반환."""
    if "@test.com" not in email and "@seed.com" not in email:
        return None
    prefix = email.split("@")[0]
    for bot_type in ENGAGEMENT_PROFILES:
        if prefix == bot_type or prefix.startswith(f"{bot_type}_"):
            return bot_type
    return None


class Command(BaseCommand):
    help = "engagement_profiles 기반으로 봇 간 좋아요 시뮬레이션"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--persona",
            type=str,
            default="",
            help="특정 봇 타입만 처리 (예: health_bot). 생략 시 전체.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="DB에 저장하지 않고 예상 좋아요 수만 출력",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="실행 전 기존 봇 좋아요를 모두 삭제 (재현 가능한 깔끔한 상태 유지)",
        )
        parser.add_argument(
            "--scale",
            type=float,
            default=_DEFAULT_SCALE,
            help=f"like_probability에 곱할 배율 (기본: {_DEFAULT_SCALE} → 실제 ~2-3%% 수준)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="랜덤 시드 (재현 가능성, 기본값: 42)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        random.seed(options["seed"])
        filter_persona: str = options["persona"]
        dry_run: bool = options["dry_run"]
        scale: float = max(0.0, min(1.0, options["scale"]))

        if dry_run:
            self.stdout.write(self.style.WARNING("[dry-run 모드] DB에 저장되지 않습니다.\n"))

        # ── 봇 유저 로드 ───────────────────────────────────────────
        bot_users = list(
            User.objects.filter(email__endswith="@test.com") | User.objects.filter(email__endswith="@seed.com")
        )
        if not bot_users:
            self.stdout.write(self.style.WARNING("봇 유저가 없습니다. seed_persona_bots를 먼저 실행하세요."))
            return

        # ── --reset: 기존 봇 좋아요 삭제 ──────────────────────────
        if options["reset"] and not dry_run:
            bot_ids = [u.pk for u in bot_users]
            deleted, _ = PostLike.objects.filter(user_id__in=bot_ids).delete()
            self.stdout.write(self.style.WARNING(f"[reset] 기존 봇 좋아요 {deleted}건 삭제\n"))

        # ── 전체 포스트 + 태그 인덱스 구축 ─────────────────────────
        all_post_ids = list(Post.objects.values_list("pk", flat=True))
        if not all_post_ids:
            self.stdout.write(self.style.WARNING("포스트가 없습니다. seed_persona_bots를 먼저 실행하세요."))
            return

        post_tag_map: dict[int, set[str]] = {}
        for pt in PostTag.objects.select_related("tag").filter(post_id__in=all_post_ids):
            post_tag_map.setdefault(pt.post_id, set()).add(pt.tag.name)

        existing_likes: set[tuple[int, int]] = set(PostLike.objects.values_list("post_id", "user_id"))

        # ── 봇 타입별 처리 ─────────────────────────────────────────
        total_created = 0
        total_skipped = 0

        for bot_type, profile in ENGAGEMENT_PROFILES.items():
            if filter_persona and bot_type != filter_persona:
                continue

            bots_of_type = [u for u in bot_users if _get_bot_type(u.email) == bot_type]
            if not bots_of_type:
                self.stdout.write(f"  [{bot_type}] 봇 없음 — 건너뜀")
                continue

            if "all" in profile.interested_tags:
                candidate_ids = all_post_ids
            else:
                candidate_ids = [pid for pid, tags in post_tag_map.items() if tags & set(profile.interested_tags)]

            if not candidate_ids:
                self.stdout.write(f"  [{bot_type}] 관심 태그 포스트 없음 — 건너뜀")
                continue

            pool_size = len(candidate_ids)
            # scale을 like_probability에만 적용 — engagement_rate는 "얼마나 볼지"이므로 유지
            effective_like_prob = profile.like_probability * scale

            new_likes: list[PostLike] = []
            bot_created = 0
            bot_skipped = 0

            for bot in bots_of_type:
                viewed_count = max(1, int(pool_size * profile.engagement_rate))
                viewed_ids = random.sample(candidate_ids, min(viewed_count, pool_size))

                for post_id in viewed_ids:
                    if random.random() > effective_like_prob:
                        continue
                    if (post_id, bot.pk) in existing_likes:
                        bot_skipped += 1
                        continue
                    new_likes.append(PostLike(post_id=post_id, user=bot))
                    existing_likes.add((post_id, bot.pk))
                    bot_created += 1

            total_created += bot_created
            total_skipped += bot_skipped

            effective_rate = profile.engagement_rate * effective_like_prob
            self.stdout.write(
                f"  [{bot_type}] 봇 {len(bots_of_type)}명 | 후보 {pool_size}개 | "
                f"유효 좋아요율 {effective_rate:.1%} | 생성 {bot_created}건"
            )

            if not dry_run and new_likes:
                PostLike.objects.bulk_create(new_likes, ignore_conflicts=True)

        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[dry-run] 총 {total_created}건 생성 예정, {total_skipped}건 중복 스킵")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"완료: 총 {total_created}건 좋아요 생성, {total_skipped}건 중복 스킵")
            )
