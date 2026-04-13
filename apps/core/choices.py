from django.db import models


class Status(models.TextChoices):
    IN_PROGRESS = "in_progress", "진행중"
    FAILED = "failed", "미달성"
    COMPLETED = "completed", "완료"


class TargetType(models.TextChoices):
    POST = "post", "게시글"
    COMMENT = "comment", "댓글"


class ReportStatus(models.TextChoices):
    PENDING = "pending", "대기중"
    HANDLED = "handled", "처리완료"
    DISMISSED = "dismissed", "기각"


class VoteStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "진행중"
    CLOSED = "closed", "종료"
    HIDDEN = "hidden", "비공개"


class CommentStatus(models.TextChoices):
    ACTIVE = "active", "활성"
    DELETED = "deleted", "삭제"


class PostStatus(models.TextChoices):
    NORMAL = "normal", "정상"
    HIDDEN = "hidden", "숨김"
    REPORTED = "reported", "신고됨"


class UserStatus(models.TextChoices):
    ACTIVE = "active", "정상"
    SUSPENDED = "suspended", "정지"
    RESTRICTED = "restricted", "제한"


class ReportReasonType(models.TextChoices):
    ABUSE = "abuse", "욕설/비하/혐오 표현"
    SPAM = "spam", "스팸/광고"
    FALSE_INFO = "false_info", "허위정보"
    SEXUAL = "sexual", "음란/선정적 컨텐츠"
    OTHER = "other", "기타"


class ReportActionType(models.TextChoices):
    DELETE = "delete", "삭제"
    KEEP = "keep", "유지"
    ABUSE = "ABUSE", "욕설/비하/혐오 표현"
    SPAM = "SPAM", "스팸/광고"
    FALSE_INFO = "FALSE_INFO", "허위정보"
    SEXUAL = "SEXUAL", "음란/선정적 컨텐츠"
    INAPPROPRIATE_PROFILE = "INAPPROPRIATE_PROFILE", "부적절한 닉네임/프로필"
    OTHER = "OTHER", "기타"


class ReportTargetType(models.TextChoices):
    POST = "POST", "게시글"
    COMMENT = "COMMENT", "댓글"
    # USER = "USER", "사용자"


class TagCategory(models.TextChoices):
    HEALTH = "HEALTH", "건강 / 운동"
    STUDY = "STUDY", "공부 / 성장"
    LIFESTYLE = "LIFESTYLE", "습관 / 라이프스타일"
    MIND = "MIND", "마음관리 / 절제"
    WORK = "WORK", "일 / 효율"
    RELATION = "RELATION", "관계 / 소통"
    FINANCE = "FINANCE", "재정 / 소비습관"
    HOBBY = "HOBBY", "취미 / 여가"
