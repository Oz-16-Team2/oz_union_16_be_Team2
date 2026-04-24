from dataclasses import dataclass
from typing import Literal


@dataclass
class BotPersona:
    """봇 페르소나 정의"""

    prefix: str
    count: int
    preferred_tags: list[str]

    # 콘텐츠 템플릿
    title_pool: list[str]
    content_pool: list[str]

    # 활동 패턴
    activity_level: Literal["low", "medium", "high"]
    posts_range: tuple[int, int]  # (min, max)
    tags_per_post: tuple[int, int]

    # 시간 패턴
    active_days_range: tuple[int, int]  # 며칠 동안 활동했나
    posting_hours: list[int]  # 주로 몇 시에 포스팅? [9, 12, 18, 22]


# ==========================================
#           페르소나 정의
# ==========================================

HEALTH_ENTHUSIAST = BotPersona(
    prefix="health_bot",
    count=30,
    preferred_tags=["건강 / 운동", "습관 / 라이프스타일"],
    title_pool=[
        "오늘도 오운완🔥",
        "헬스장 출석!",
        "식단 기록 1일차",
        "런닝 5km 완료",
        "PT 10회차 후기",
        "단백질 쉐이크 추천템",
    ],
    content_pool=[
        "열심히 땀 흘렸습니다.",
        "근육통이 장난 아니네요.",
        "건강해지는 기분!",
        "오늘도 꾸준히 실천 중입니다.",
        "목표 체중까지 화이팅!",
    ],
    activity_level="high",
    posts_range=(8, 15),
    tags_per_post=(2, 4),
    active_days_range=(60, 90),
    posting_hours=[6, 7, 18, 19, 20],  # 아침/저녁 운동 시간
)

MIRACLE_MORNING_USER = BotPersona(
    prefix="miracle_bot",
    count=30,
    preferred_tags=["공부 / 성장", "일 / 효율", "마음관리 / 절제"],
    title_pool=[
        "미라클 모닝 성공☀️",
        "파이썬 알고리즘 공부",
        "독서 기록",
        "오늘의 업무 회고",
        "새벽 5시 기상",
        "목표 달성 체크리스트",
    ],
    content_pool=[
        "아침 6시 기상 완벽",
        "새로운 지식을 얻었습니다.",
        "집중력이 좋았던 하루!",
        "계획대로 실천 중입니다.",
        "성장하는 기분이 좋네요.",
    ],
    activity_level="medium",
    posts_range=(5, 10),
    tags_per_post=(1, 3),
    active_days_range=(30, 60),
    posting_hours=[5, 6, 7, 22, 23],  # 새벽/밤 기록 시간
)

CASUAL_USER = BotPersona(
    prefix="random_bot",
    count=20,
    preferred_tags=["all"],  # 특별한 선호 없음
    title_pool=["오늘의 일상", "그냥 끄적여봅니다", "날씨가 좋네요", "주말 나들이"],
    content_pool=[
        "아침 6시 기상 완벽",
        "새로운 지식을 얻었습니다.",
        "집중력이 좋았던 하루!",
        "계획대로 실천 중입니다.",
        "성장하는 기분이 좋네요.",
    ],
    activity_level="low",
    posts_range=(1, 3),
    tags_per_post=(0, 2),
    active_days_range=(7, 30),
    posting_hours=[12, 13, 20, 21, 22],  # 점심/저녁 시간
)

NIGHT_OWL = BotPersona(
    prefix="night_owl",
    count=15,
    preferred_tags=["개발 / 코딩", "공부 / 성장"],
    title_pool=["오늘의 일상", "그냥 끄적여봅니다", "날씨가 좋네요", "주말 나들이"],
    content_pool=["평범한 하루였습니다.", "내일도 화이팅!", "잘 쉬었습니다."],
    activity_level="low",
    posts_range=(1, 3),
    tags_per_post=(0, 2),
    active_days_range=(7, 30),
    posting_hours=[23, 0, 1, 2, 3],  # 야행성
)

# 모든 페르소나 리스트
ALL_PERSONAS = [
    HEALTH_ENTHUSIAST,
    MIRACLE_MORNING_USER,
    CASUAL_USER,
    NIGHT_OWL,
]
