from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.interfaces.auth_user_repository import AuthUserRepository
from app.domain.entities.auth_user import AuthUser
from app.infrastructure.db.models.auth_user_model import AuthUserModel


class SqlAlchemyAuthUserRepository(AuthUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_username(self, username: str) -> AuthUser | None:
        statement = select(AuthUserModel).where(AuthUserModel.username == username)
        model = self._session.execute(statement).scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    def create_user(
        self,
        username: str,
        password_hash: str,
        display_name: str | None = None,
        is_admin: bool = False,
        is_active: bool = True,
    ) -> AuthUser:
        model = AuthUserModel(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            is_admin=is_admin,
            is_active=is_active,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def touch_last_login(self, username: str) -> None:
        statement = select(AuthUserModel).where(AuthUserModel.username == username)
        model = self._session.execute(statement).scalar_one_or_none()
        if not model:
            return
        model.last_login_at = datetime.now(UTC)
        self._session.add(model)
        self._session.commit()

    @staticmethod
    def _to_domain(model: AuthUserModel) -> AuthUser:
        return AuthUser(
            username=model.username,
            display_name=model.display_name,
            password_hash=model.password_hash,
            is_active=model.is_active,
            is_admin=model.is_admin,
            last_login_at=model.last_login_at,
        )
