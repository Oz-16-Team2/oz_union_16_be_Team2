"""
추천 알고리즘 튜닝 파라미터 중앙 관리.
수치를 바꾸고 싶을 때 이 파일만 수정하면 됩니다.
"""

# ── 공통 ──────────────────────────────────────────────
CONTENT_PREVIEW_LENGTH: int = 100  # 게시글 미리보기 글자 수

# ── 맞춤형 추천 (Content-Based Filtering) ─────────────
# 태그 점수: 내가 작성/좋아요한 글의 태그에 부여하는 가중치
SUGGESTION_AUTHORED_WEIGHT: float = 5.0
SUGGESTION_LIKED_WEIGHT: float = 3.0

# 시간 감가율: max(0.1, 1 - 나이(일) / MAX_DAYS)
# MAX_DAYS 이상 된 글은 최솟값 0.1로 고정
SUGGESTION_TIME_DECAY_MAX_DAYS: float = 20.0

# 추천 후보 상한 (DB → Python 정렬 전 최대 로드 수)
SUGGESTION_CANDIDATE_LIMIT: int = 100

# ── 인기 게시글 (Trending) ────────────────────────────
# Hot Score = like_count / (age_hours + 2) ** GRAVITY
# gravity 클수록 오래된 글이 빠르게 순위 하락
TRENDING_HOT_SCORE_GRAVITY: float = 1.7

# week 모드: like_count 상위 N개만 Python으로 hot score 계산 (메모리 제한)
TRENDING_WEEK_CANDIDATE_LIMIT: int = 500

TRENDING_PERIOD_DAYS: dict[str, int] = {
    "day": 1,  # 지금 핫한 글 (24시간) — DB 정렬
    "week": 7,  # 요즘 뜨는 글 (7일)   — Hot Score 정렬
}
TRENDING_DEFAULT_PERIOD: str = "week"
