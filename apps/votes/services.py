from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.serializers import ValidationError

from apps.core.choices import VoteStatus
from apps.core.exceptions import ResourceNotFoundException
from apps.posts.models import Post
from apps.votes.models import Vote, VoteOption, VoteParticipation


@transaction.atomic
def create_vote(
    *,
    post_id: int,
    options: list[str],
    start_at: Any,
    end_at: Any,
) -> dict[str, Any]:
    post = Post.objects.filter(id=post_id, deleted_at__isnull=True).first()
    if post is None:
        raise NotFound("해당 게시글을 찾을 수 없습니다.")

    if Vote.objects.filter(post=post).exists():
        raise ValidationError("투표 입력값이 올바르지 않습니다.")

    vote = Vote.objects.create(
        post=post,
        start_at=start_at,
        end_at=end_at,
        status=VoteStatus.IN_PROGRESS,
    )
    VoteOption.objects.bulk_create(
        [VoteOption(vote=vote, content=option, sort_order=index) for index, option in enumerate(options, start=1)]
    )
    vote.refresh_from_db()

    options_payload = [
        {
            "vote_option_id": opt.id,
            "content": opt.content,
            "sort_order": opt.sort_order,
        }
        for opt in vote.options.all().order_by("sort_order")
    ]

    return {
        "vote_id": vote.id,
        "post_id": post.id,
        "start_at": vote.start_at,
        "end_at": vote.end_at,
        "status": vote.status.upper(),
        "options": options_payload,
    }


@transaction.atomic
def create_default_vote_for_post(post: Post, vote_data: dict[str, Any]) -> None:
    now = timezone.now()
    vote = Vote.objects.create(
        post=post,
        start_at=now,
        end_at=vote_data["end_at"],
        status=VoteStatus.IN_PROGRESS,
    )
    VoteOption.objects.bulk_create(
        [
            VoteOption(vote=vote, content=option["content"], sort_order=option["sort_order"])
            for option in vote_data["options"]
        ]
    )


@transaction.atomic
def participate_vote(
    *,
    vote_id: int,
    user: Any,
    option_id: int,
) -> dict[str, Any]:
    vote = Vote.objects.filter(id=vote_id).first()
    if vote is None:
        raise NotFound("해당 투표를 찾을 수 없습니다.")

    if vote.status != VoteStatus.IN_PROGRESS:
        raise ValidationError("진행 중인 투표가 아닙니다.")

    option = VoteOption.objects.filter(id=option_id, vote=vote).first()
    if option is None:
        raise ValidationError("유효한 투표 옵션이 필요합니다.")

    if VoteParticipation.objects.filter(vote=vote, user=user).exists():
        raise ValidationError("이미 참여한 투표입니다.")

    participation = VoteParticipation.objects.create(
        vote=vote,
        user=user,
        vote_option=option,
    )

    return {
        "vote_id": vote.id,
        "vote_option_id": option.id,
        "user_id": getattr(user, "id", None),
        "created_at": participation.created_at,
    }


@transaction.atomic
def update_vote(
    *,
    vote_id: int,
    user: Any,
    options: list[str],
    start_at: Any,
    end_at: Any,
) -> dict[str, Any]:
    vote = Vote.objects.filter(id=vote_id).first()
    if vote is None:
        raise NotFound("해당 투표를 찾을 수 없습니다.")

    if vote.post.user_id != user.id:
        raise ValidationError("투표를 수정할 권한이 없습니다.")

    if vote.participations.exists():
        raise ValidationError("이미 참여자가 있는 투표는 수정할 수 없습니다.")

    if vote.status != VoteStatus.IN_PROGRESS:
        raise ValidationError("진행 중인 투표만 수정할 수 있습니다.")

    vote.start_at = start_at
    vote.end_at = end_at
    vote.save()

    vote.options.all().delete()

    VoteOption.objects.bulk_create(
        [
            VoteOption(
                vote=vote,
                content=option,
                sort_order=index,
            )
            for index, option in enumerate(options, start=1)
        ]
    )

    vote.refresh_from_db()

    options_payload = [
        {"vote_option_id": o.id, "content": o.content, "sort_order": o.sort_order}
        for o in vote.options.all().order_by("sort_order")
    ]

    return {
        "vote_id": vote.id,
        "start_at": vote.start_at,
        "end_at": vote.end_at,
        "status": vote.status,
        "options": options_payload,
    }


@transaction.atomic
def delete_vote(*, vote_id: int, user: Any) -> None:
    vote = Vote.objects.filter(id=vote_id).first()
    if vote is None:
        raise ResourceNotFoundException("해당 투표를 찾을 수 없습니다.")

    if vote.post.user_id != user.id:
        raise ValidationError("투표를 삭제할 권한이 없습니다.")

    if vote.participations.exists():
        raise ValidationError("이미 참여자가 있는 투표는 삭제할 수 없습니다.")

    vote.delete()
    return None


def get_vote_detail(*, vote_id: int) -> dict[str, Any]:
    vote = Vote.objects.filter(id=vote_id).prefetch_related("participations", "options__participations").first()
    if vote is None:
        raise NotFound("해당 투표를 찾을 수 없습니다.")

    total_count = vote.participations.count()

    options_payload = []
    for option in vote.options.all().order_by("sort_order"):
        count = option.participations.count()
        rate = round((count / total_count) * 100, 2) if total_count > 0 else 0.00
        options_payload.append(
            {
                "vote_option_id": option.id,
                "content": option.content,
                "count": count,
                "rate": rate,
            }
        )
    return {
        "vote_id": vote.id,
        "status": vote.status,
        "total_count": total_count,
        "options": options_payload,
    }
