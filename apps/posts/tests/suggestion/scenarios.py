from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.posts.tests.suggestion.personas import (
    CASUAL_USER,
    HEALTH_ENTHUSIAST,
    MIRACLE_MORNING_USER,
    NIGHT_OWL,
    BotPersona,
)


@dataclass
class TestScenario:
    """테스트 시나리오"""

    name: str
    description: str
    personas: list[BotPersona]

    enable_engagement: bool = True
    enable_time_distribution: bool = True

    # spike_tag, spike_days, spike_multiplier 키를 가질 수 있음
    extra_config: dict[str, Any] = field(default_factory=dict)


# 시나리오 1: 기본 추천 알고리즘 테스트
# 생성 봇: health_bot(30) + miracle_bot(30) + random_bot(20) + night_owl(15) = 총 95명
BASIC_RECOMMENDATION_TEST = TestScenario(
    name="basic_recommendation",
    description="다양한 성향의 봇 4종으로 구성된 기본 추천 생태계",
    personas=[HEALTH_ENTHUSIAST, MIRACLE_MORNING_USER, CASUAL_USER, NIGHT_OWL],
    enable_engagement=True,
    enable_time_distribution=True,
)

# 시나리오 2: 콜드 스타트 테스트
# 생성 봇: random_bot(20, 기존 콘텐츠) + newbie_bot(10, 활동 없는 신규)
COLD_START_TEST = TestScenario(
    name="cold_start",
    description="활동 이력 없는 신규 유저에게 Fallback 추천이 제공되는지 검증",
    personas=[
        CASUAL_USER,
        BotPersona(
            prefix="newbie_bot",
            count=10,
            preferred_tags=["all"],
            title_pool=["첫 포스팅"],
            content_pool=["안녕하세요"],
            activity_level="low",
            posts_range=(1, 2),
            tags_per_post=(0, 1),
            active_days_range=(1, 3),
            posting_hours=[12],
        ),
    ],
    enable_engagement=False,
)

# 시나리오 3: 트렌드 감지 테스트
# 생성 봇: health_bot(30) + miracle_bot(30) 배경 데이터
#          + spike_tag("건강 / 운동")가 최근 spike_days(3일)간 spike_multiplier(5)배 급증
TREND_DETECTION_TEST = TestScenario(
    name="trend_detection",
    description="특정 태그가 최근 급증할 때 추천 순위가 올라가는지 검증",
    personas=[HEALTH_ENTHUSIAST, MIRACLE_MORNING_USER],
    extra_config={
        "spike_tag": "건강 / 운동",
        "spike_days": 3,
        "spike_multiplier": 5,
    },
)
