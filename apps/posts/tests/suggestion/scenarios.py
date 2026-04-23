from dataclasses import dataclass

from apps.posts.tests.suggestion.personas import (
    CASUAL_USER,
    HEALTH_ENTHUSIAST,
    MIRACLE_MORNING_USER,
    BotPersona,
)


@dataclass
class TestScenario:
    """테스트 시나리오"""

    name: str
    description: str
    personas: list[BotPersona]

    # 시나리오별 특수 설정
    enable_engagement: bool = True
    enable_time_distribution: bool = True

    extra_config: dict = None


# 시나리오 1: 기본 추천 알고리즘 테스트
BASIC_RECOMMENDATION_TEST = TestScenario(
    name="basic_recommendation",
    description="기본적인 협업 필터링 추천 테스트",
    personas=[HEALTH_ENTHUSIAST, MIRACLE_MORNING_USER, CASUAL_USER],
    enable_engagement=True,
    enable_time_distribution=True,
)

# 시나리오 2: 콜드 스타트 테스트
COLD_START_TEST = TestScenario(
    name="cold_start",
    description="신규 유저 추천 테스트",
    personas=[
        CASUAL_USER,  # 기존 유저
        BotPersona(  # 신규 유저
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
    enable_engagement=False,  # 신규라 engagement 없음.
)

# 시나리오 3: 트렌드 감지 테스트
TREND_DETECTION_TEST = TestScenario(
    name="trend_detection",
    description="급부상 태그 감지 테스트",
    personas=[HEALTH_ENTHUSIAST],
    extra_config={
        "create_trending_spike": True,
        "spike_tag": "건강 / 운동",
        "spike_days": 3,  # 최근 3일간 급증
        "spike_multiplier": 5,  # 5배 증가
    },
)
