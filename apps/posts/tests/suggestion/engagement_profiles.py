from dataclasses import dataclass


@dataclass
class EngagementProfile:
    """봇의 engagement 행동 패턴"""

    bot_type: str

    # 어떤 태그에 관심있나
    interested_tags: list[str]

    # 얼마나 적극적인가
    engagement_rate: float  # 관심 포스트의 몇 %에 반응?
    like_probability: float  # 좋아요 확률
    comment_probability: float  # 댓글 확률

    # 댓글 템플릿
    comment_templates: list[str]


ENGAGEMENT_PROFILES = {
    "health_bot": EngagementProfile(
        bot_type="health_bot",
        interested_tags=["건강 / 운동", "습관 / 라이프스타일", "공부 / 성장"],
        engagement_rate=0.35,
        like_probability=0.7,
        comment_probability=0.25,
        comment_templates=[
            "저도 운동 열심히 하고 있어요!",
            "화이팅입니다!",
            "부럽네요 ㅎㅎ",
            "저도 같은 루틴 따라해볼게요",
            "대단하시네요!",
        ],
    ),
    "miracle_bot": EngagementProfile(
        bot_type="miracle_bot",
        interested_tags=["공부 / 성장", "일 / 효율", "마음관리 / 절제", "건강 / 운동"],
        engagement_rate=0.4,
        like_probability=0.6,
        comment_probability=0.35,
        comment_templates=[
            "좋은 인사이트네요.",
            "저도 실천해봐야겠습니다.",
            "공감됩니다!",
            "어떤 책 읽으셨나요?",
            "구체적인 방법이 궁금합니다.",
        ],
    ),
    "random_bot": EngagementProfile(
        bot_type="random_bot",
        interested_tags=["all"],
        engagement_rate=0.08,  # 잠수 유저
        like_probability=0.4,
        comment_probability=0.05,
        comment_templates=["좋아요!", "ㅎㅎ", "굿", "👍"],
    ),
}
