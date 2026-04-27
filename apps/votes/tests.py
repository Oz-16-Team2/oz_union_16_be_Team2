from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.choices import VoteStatus
from apps.posts.models import Post
from apps.users.models import User  # 추가 (실제 경로 맞게 수정)
from apps.votes.models import Vote, VoteOption
from apps.votes.services import create_vote, update_vote


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
            question="운동하셨나요?",
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
            question="원래 질문",
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
            question="수정된 질문",
            options=["찬성", "반대"],
            start_at=start_at,
            end_at=end_at,
        )

        assert result["vote_id"] == vote.id
