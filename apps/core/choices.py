from django.db import models


class Status(models.TextChoices):
    IN_PROGRESS = "in_progress", "진행중"
    FAILED = "failed", "미달성"
    COMPLETED = "completed", "완료"


class TargetType(models.TextChoices):
    POST = "POST", "게시글"
    COMMENT = "COMMENT", "댓글"
    USER = "USER", "유저"


class ReportStatus(models.TextChoices):
    PENDING = "pending", "대기중"
    HANDLED = "handled", "처리완료"
    DISMISSED = "dismissed", "기각"


class VoteStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "진행중"
    CLOSED = "closed", "종료"
    HIDDEN = "hidden", "비공개"


class CommentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "활성"
    DELETED = "DELETED", "삭제"


class PostStatus(models.TextChoices):
    NORMAL = "normal", "정상"
    HIDDEN = "hidden", "숨김"
    REPORTED = "reported", "신고됨"


class UserStatus(models.TextChoices):
    ACTIVE = "active", "정상"
    SUSPENDED = "suspended", "정지"
    RESTRICTED = "restricted", "제한"
