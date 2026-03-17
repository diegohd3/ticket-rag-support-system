from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.support_user import SupportUser


class SupportUserRepository(ABC):
    @abstractmethod
    def get_or_create(self, user_id: str, display_name: str | None = None) -> SupportUser:
        raise NotImplementedError

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> SupportUser | None:
        raise NotImplementedError

    @abstractmethod
    def increment_violation(
        self,
        user_id: str,
        reason: str,
        threshold: int,
    ) -> SupportUser:
        raise NotImplementedError

    @abstractmethod
    def reset_violations(self, user_id: str) -> None:
        raise NotImplementedError
