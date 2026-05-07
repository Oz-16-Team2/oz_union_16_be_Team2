from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.serializers import ValidationError

from apps.core.choices import VoteStatus
from apps.posts.models import Post
from apps.users.models import User
from apps.votes.models import Vote, VoteOption
from apps.votes.services import create_vote, get_vote_detail, participate_vote, update_vote


@pytest.fixture
def other_user(db: None) -> User:
    return User.objects.create_user(
        email="other@test.com",
        password="1234",
        nickname="other",
    )


@pytest.fixture
def vote_owner(db: None) -> User:
    return User.objects.create_user(
        email="vote-owner@test.com",
        password="1234",
        nickname="vote-owner",
    )


@pytest.fixture
def vote_post(
    db: None,
    vote_owner: User,
) -> Post:
    return Post.objects.create(
        user=vote_owner,
        title="투표 게시글",
        content="내용",
        is_private=False,
    )


@pytest.mark.django_db
class TestVoteServices:
    def test_create_vote_response_matches_serializer_contract(
        self,
        vote_post: Post,
    ) -> None:
        start_at = timezone.now()
        end_at = start_at + timedelta(days=2)

        result = create_vote(
            post_id=vote_post.id,
            options=["예", "아니오"],
            start_at=start_at,
            end_at=end_at,
        )

        assert result["post_id"] == vote_post.id

    def test_update_vote_response_matches_serializer_contract(
        self,
        vote_owner: User,
        vote_post: Post,
    ) -> None:
        start_at = timezone.now()
        end_at = start_at + timedelta(days=2)

        vote = Vote.objects.create(
            post=vote_post,
            start_at=start_at,
            end_at=end_at,
            status=VoteStatus.IN_PROGRESS,
        )

        VoteOption.objects.bulk_create(
            [
                VoteOption(vote=vote, content="원본 1", sort_order=1),
                VoteOption(vote=vote, content="원본 2", sort_order=2),
            ]
        )

        result = update_vote(
            vote_id=vote.id,
            user=vote_owner,
            options=["찬성", "반대"],
            start_at=start_at,
            end_at=end_at,
        )

        assert result["vote_id"] == vote.id

    def test_get_vote_detail_status_closed_after_end_at(
        self,
        vote_post: Post,
        vote_owner: User,
    ) -> None:
        # 이미 종료된 투표 생성
        yesterday = timezone.now() - timedelta(days=1)
        vote = Vote.objects.create(
            post=vote_post,
            start_at=yesterday - timedelta(days=1),
            end_at=yesterday,
            status=VoteStatus.IN_PROGRESS,
        )

        result = get_vote_detail(vote_id=vote.id, user=vote_owner)

        # DB에는 in_progress여도 반환값은 closed여야 함
        assert result["status"] == VoteStatus.CLOSED

    def test_participate_vote_fails_after_end_at(
        self,
        vote_post: Post,
        other_user: User,
    ) -> None:
        # 이미 종료된 투표 생성
        yesterday = timezone.now() - timedelta(days=1)
        vote = Vote.objects.create(
            post=vote_post,
            start_at=yesterday - timedelta(days=1),
            end_at=yesterday,
            status=VoteStatus.IN_PROGRESS,
        )
        option = VoteOption.objects.create(vote=vote, content="옵션", sort_order=1)

        # 종료된 투표에 참여 시도 시 ValidationError 발생해야 함
        with pytest.raises(ValidationError) as excinfo:
            participate_vote(
                vote_id=vote.id,
                user=other_user,
                option_id=option.id,
            )

        assert "종료된 투표입니다." in str(excinfo.value)
