from __future__ import annotations

from apps.core.exceptions import ConflictException, ResourceNotFoundException
from apps.posts.models import Tag


class AdminTagService:
    @staticmethod
    def get_tags(*, page: int, size: int) -> list[Tag]:
        offset = (page - 1) * size
        limit = offset + size

        return list(Tag.objects.order_by("-created_at")[offset:limit])

    @staticmethod
    def create_tag(*, name: str) -> Tag:
        if Tag.objects.filter(name=name).exists():
            raise ConflictException("이미 존재하는 태그입니다.")

        return Tag.objects.create(name=name)

    @staticmethod
    def update_tag_status(*, tag_id: int, is_active: bool) -> Tag:
        try:
            tag = Tag.objects.get(id=tag_id)
        except Tag.DoesNotExist as exc:
            raise ResourceNotFoundException("태그를 찾을 수 없습니다.") from exc

        tag.is_active = is_active
        tag.save(update_fields=["is_active"])

        return tag
