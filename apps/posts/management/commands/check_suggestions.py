"""
페르소나별 추천 품질을 DB 봇 데이터 기반으로 출력합니다.

사전 조건:
  1. python manage.py seed_tag
  2. python manage.py seed_persona_bots --scenario basic (또는 trend)
  3. python manage.py seed_engagement --reset

사용법:
  python manage.py check_suggestions
  python manage.py check_suggestions --persona health_bot
  python manage.py check_suggestions --min-posts 3
"""

from __future__ import annotations

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from apps.posts.services.persona_analysis_service import analyze_by_persona
from apps.posts.tests.suggestion.engagement_profiles import ENGAGEMENT_PROFILES


class Command(BaseCommand):
    help = "페르소나별 추천 품질(tag_precision 중심) 리포트 출력"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--persona",
            type=str,
            default="",
            help="특정 페르소나만 확인 (예: health_bot). 생략 시 전체 출력.",
        )
        parser.add_argument(
            "--min-posts",
            type=int,
            default=1,
            help="집계에 포함할 봇의 최소 추천 결과 수 (기본값: 1)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        filter_persona: str = options["persona"]
        min_posts: int = options["min_posts"]

        self.stdout.write("\n추천 품질 분석 중...\n")

        persona_tags = {k: v.interested_tags for k, v in ENGAGEMENT_PROFILES.items()}
        results = analyze_by_persona(persona_interested_tags=persona_tags)

        if not results:
            self.stdout.write(self.style.WARNING("봇 데이터가 없습니다. seed_persona_bots를 먼저 실행하세요."))
            return

        for persona, user_metrics in sorted(results.items()):
            if filter_persona and persona != filter_persona:
                continue

            valid = [m for m in user_metrics.values() if m["count"] >= min_posts]
            if not valid:
                continue

            avg_count = sum(m["count"] for m in valid) / len(valid)
            total_hits = sum(m["hits"] for m in valid)
            avg_precision = sum(m["precision"] for m in valid) / len(valid)
            avg_random = sum(m["random_baseline"] for m in valid) / len(valid)
            avg_lift = sum(m["lift"] for m in valid) / len(valid)

            tag_prec_values = [m["tag_precision"] for m in valid if m["tag_precision"] is not None]
            avg_tag_prec: float | None = sum(tag_prec_values) / len(tag_prec_values) if tag_prec_values else None

            # ── 등급: CBF의 핵심 지표인 tag_precision 기준 ──────────
            if avg_tag_prec is not None:
                if avg_tag_prec >= 0.9:
                    grade = self.style.SUCCESS("● 우수")
                elif avg_tag_prec >= 0.7:
                    grade = self.style.WARNING("● 보통")
                else:
                    grade = self.style.ERROR("● 미흡")
                grade_basis = "tag_precision"
            else:
                # "all" 태그 타입은 tag_precision 없으므로 lift 기준
                if avg_lift >= 2.0:
                    grade = self.style.SUCCESS("● 우수")
                elif avg_lift >= 1.0:
                    grade = self.style.WARNING("● 보통")
                else:
                    grade = self.style.ERROR("● 미흡")
                grade_basis = "lift"

            self.stdout.write(f"[{persona}]  {grade}  ({grade_basis} 기준)")
            self.stdout.write(f"  봇 수           : {len(valid)}명")
            self.stdout.write(f"  평균 추천 수    : {avg_count:.1f}개")

            # 1차 지표: tag_precision (CBF 핵심)
            if avg_tag_prec is not None:
                self.stdout.write(f"  tag precision ★ : {avg_tag_prec:.2%}  ← 관심 태그 게시글 추천 비율")
            else:
                self.stdout.write("  tag precision ★ : N/A  (관심 태그가 'all')")

            # 2차 지표: precision / lift (참고용)
            self.stdout.write(f"  precision  (참고): {avg_precision:.2%}  (이미 좋아요한 글 적중률)")
            self.stdout.write(f"  random baseline : {avg_random:.2%}  (좋아요수/전체글 — 봇 활동량 지표)")
            self.stdout.write(f"  lift       (참고): {avg_lift:.1f}x   (precision ÷ random_baseline)")
            self.stdout.write(f"  총 히트 수      : {total_hits}건")
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("분석 완료."))
        self.stdout.write(
            "\n  [지표 해석]\n"
            "  tag precision ★ = 추천 게시글 중 봇의 관심 태그가 포함된 비율\n"
            "                    CBF 알고리즘의 핵심 지표. 90% 이상이면 정상 동작.\n"
            "  precision (참고) = 추천 중 봇이 '이미 좋아요한' 글 비율\n"
            "                    CBF는 새 글을 찾아주는 것이 목적이므로 낮아도 정상.\n"
            "  lift      (참고) = precision ÷ random_baseline\n"
            "                    random_baseline이 높으면(봇 활동량 과다) 왜곡됨.\n"
        )
