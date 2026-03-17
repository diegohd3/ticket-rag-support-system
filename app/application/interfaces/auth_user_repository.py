from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.auth_user import AuthUser


class AuthUserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> AuthUser | None:
        raise NotImplementedError

    @abstractmethod
    def create_user(
        self,
        username: str,
        password_hash: str,
        display_name: str | None = None,
        is_admin: bool = False,
        is_active: bool = True,
    ) -> AuthUser:
        raise NotImplementedError

    @abstractmethod
    def touch_last_login(self, username: str) -> None:
        raise NotImplementedError
