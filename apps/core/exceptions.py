from __future__ import annotations


class ConflictException(Exception):
    def __init__(self, detail: object) -> None:
        self.detail = detail
        super().__init__(str(detail))


class ResourceNotFoundException(Exception):
    def __init__(self, detail: object) -> None:
        self.detail = detail
        super().__init__(str(detail))
