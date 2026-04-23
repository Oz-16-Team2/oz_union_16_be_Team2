"""
Factory Boy + Faker 기반 테스트 데이터 팩토리.

factory-boy 3.3+는 py.typed를 포함하며 Factory[T] 제네릭을 지원한다.
DjangoModelFactory[Model]로 서브클래싱하면 .create()가 올바른 반환 타입을 가진다.

mypy strict 호환 전략:
  - factory 선언자(LazyAttribute 등)를 소스 모듈에서 직접 import해 attr-defined 오류 방지
  - LazyAttribute / Sequence / SubFactory / Faker의 __init__이 untyped이므로
    각 선언에 # type: ignore[no-untyped-call] 적용 (불가피한 factory-boy 한계)
  - 클래스 본문 필드에는 타입 어노테이션을 붙이지 않음
    (factory 선언자 반환 타입이 실제 필드 타입과 달라 assignment 오류 유발)
  - 모듈 레벨 typed 헬퍼 함수로 반환 타입을 보장
"""

from __future__ import annotations

from typing import Any

from factory.declarations import LazyAttribute, Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from apps.posts.models import Post, PostLike, PostTag, Tag
from apps.users.models import User

# ── 팩토리 클래스 ──────────────────────────────────────────────────


class UserFactory(DjangoModelFactory[User]):
    class Meta:
        model = User

    email = LazyAttribute(lambda obj: f"{obj.nickname}@example.com")  # type: ignore[no-untyped-call]
    nickname = Sequence(lambda n: f"user_{n}")  # type: ignore[no-untyped-call]
    password = "pbkdf2_sha256$dummy_hash_for_tests!"
    is_active = True


class BotUserFactory(DjangoModelFactory[User]):
    """@test.com 도메인 봇 유저 (production 환경 필터링 대상)."""

    class Meta:
        model = User

    email = LazyAttribute(lambda obj: f"{obj.nickname}@test.com")  # type: ignore[no-untyped-call]
    nickname = Sequence(lambda n: f"bot_{n}")  # type: ignore[no-untyped-call]
    password = "pbkdf2_sha256$dummy_hash_for_tests!"
    is_active = True


class TagFactory(DjangoModelFactory[Tag]):
    class Meta:
        model = Tag
        django_get_or_create = ("name",)

    name = Sequence(lambda n: f"태그_{n}")  # type: ignore[no-untyped-call]
    is_active = True


class PostFactory(DjangoModelFactory[Post]):
    class Meta:
        model = Post

    user = SubFactory(UserFactory)  # type: ignore[no-untyped-call]
    title = Faker("sentence", nb_words=4, locale="ko_KR")  # type: ignore[no-untyped-call]
    content = Faker("paragraph", nb_sentences=3, locale="ko_KR")  # type: ignore[no-untyped-call]


class PostTagFactory(DjangoModelFactory[PostTag]):
    class Meta:
        model = PostTag
        django_get_or_create = ("post", "tag")

    post = SubFactory(PostFactory)  # type: ignore[no-untyped-call]
    tag = SubFactory(TagFactory)  # type: ignore[no-untyped-call]


class PostLikeFactory(DjangoModelFactory[PostLike]):
    class Meta:
        model = PostLike
        django_get_or_create = ("post", "user")

    post = SubFactory(PostFactory)  # type: ignore[no-untyped-call]
    user = SubFactory(UserFactory)  # type: ignore[no-untyped-call]


# ── Typed 헬퍼 함수 ───────────────────────────────────────────────
# 외부에서 팩토리를 호출할 때 정확한 반환 타입을 제공한다.


def UserFactory_create(**kwargs: Any) -> User:
    return UserFactory.create(**kwargs)


def BotUserFactory_create(**kwargs: Any) -> User:
    return BotUserFactory.create(**kwargs)


def TagFactory_create(**kwargs: Any) -> Tag:
    return TagFactory.create(**kwargs)


def PostFactory_create(**kwargs: Any) -> Post:
    return PostFactory.create(**kwargs)


def PostTagFactory_create(**kwargs: Any) -> PostTag:
    return PostTagFactory.create(**kwargs)


def PostLikeFactory_create(**kwargs: Any) -> PostLike:
    return PostLikeFactory.create(**kwargs)
