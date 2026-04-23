from django.core.management.base import BaseCommand, CommandError

from apps.posts.models import Tag
from apps.posts.tests.suggestion.bot_factory import BotFactory
from apps.posts.tests.suggestion.scenarios import (
    BASIC_RECOMMENDATION_TEST,
    COLD_START_TEST,
    TREND_DETECTION_TEST,
)

SCENARIOS = {
    "basic": BASIC_RECOMMENDATION_TEST,
    "cold_start": COLD_START_TEST,
    "trend": TREND_DETECTION_TEST,
}


class Command(BaseCommand):
    help = "페르소나 봇 및 테스트 데이터 생성"

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        if options["list"]:
            self.stdout.write("사용 가능한 시나리오:")
            for key, scenario in SCENARIOS.items():
                self.stdout.write(f"  {key}: {scenario.description}")
            return

        scenario = SCENARIOS[options["scenario"]]
        self.stdout.write(f"시나리오: {scenario.name} — {scenario.description}")

        all_tags = list(Tag.objects.filter(is_active=True))
        if not all_tags:
            raise CommandError("태그가 없습니다. 먼저 seed_tag 커맨드를 실행하세요.")

        for persona in scenario.personas:
            factory = BotFactory(persona, all_tags)
            bots, posts = factory.create_bots_with_posts()
            self.stdout.write(self.style.SUCCESS(f"[{persona.prefix}] 유저 {len(bots)}명, 포스트 {len(posts)}개 생성"))

        self.stdout.write(self.style.SUCCESS("완료!"))
