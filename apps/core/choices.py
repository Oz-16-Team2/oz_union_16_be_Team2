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


class ProfileImageCode(models.TextChoices):
    AVATAR_01 = "avatar_1", "캐릭터 1"
    AVATAR_02 = "avatar_2", "캐릭터 2"
    AVATAR_03 = "avatar_3", "캐릭터 3"
    AVATAR_04 = "avatar_4", "캐릭터 4"
