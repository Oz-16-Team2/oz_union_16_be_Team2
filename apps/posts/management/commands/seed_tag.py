from typing import Any

from django.core.management.base import BaseCommand

from apps.posts.models import Tag


class Command(BaseCommand):
    help = "기획된 8개의 기본 카테고리 태그를 DB에 생성합니다."

    def handle(self, *args: Any, **options: Any) -> None:
        default_tags = [
            "건강 / 운동",
            "공부 / 성장",
            "습관 / 라이프스타일",
            "마음관리 / 절제",
            "일 / 효율",
            "관계 / 소통",
            "재정 / 소비습관",
            "취미 / 여가",
        ]

        for tag_name in default_tags:
            # get_or_create, 이미 존재하는 태그 필터
            tag, created = Tag.objects.get_or_create(name=tag_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f" 태그 생성 완료: {tag_name}"))
            else:
                self.stdout.write(self.style.WARNING(f" 이미 존재하는 태그: {tag_name}"))

        self.stdout.write(self.style.SUCCESS("🎉 모든 기본 태그 세팅이 완료되었습니다!"))
