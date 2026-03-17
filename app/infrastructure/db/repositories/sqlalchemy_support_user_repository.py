from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.interfaces.support_user_repository import SupportUserRepository
from app.domain.entities.support_user import SupportUser
from app.infrastructure.db.models.support_user_model import SupportUserModel


class SqlAlchemySupportUserRepository(SupportUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create(self, user_id: str, display_name: str | None = None) -> SupportUser:
        statement = select(SupportUserModel).where(SupportUserModel.user_id == user_id)
        model = self._session.execute(statement).scalar_one_or_none()
        if not model:
            model = SupportUserModel(
                user_id=user_id,
                display_name=display_name,
                last_seen_at=datetime.now(UTC),
            )
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
            return self._to_domain(model)

        if display_name and display_name != model.display_name:
            model.display_name = display_name
        model.last_seen_at = datetime.now(UTC)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def get_by_user_id(self, user_id: str) -> SupportUser | None:
        statement = select(SupportUserModel).where(SupportUserModel.user_id == user_id)
        model = self._session.execute(statement).scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    def increment_violation(
        self,
        user_id: str,
        reason: str,
        threshold: int,
    ) -> SupportUser:
        statement = select(SupportUserModel).where(SupportUserModel.user_id == user_id)
        model = self._session.execute(statement).scalar_one_or_none()
        if not model:
            model = SupportUserModel(user_id=user_id, violation_count=0)

        model.violation_count += 1
        model.last_seen_at = datetime.now(UTC)
        if model.violation_count >= threshold:
            model.is_blocked = True
            model.blocked_reason = reason
            model.blocked_at = datetime.now(UTC)

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def reset_violations(self, user_id: str) -> None:
        statement = select(SupportUserModel).where(SupportUserModel.user_id == user_id)
        model = self._session.execute(statement).scalar_one_or_none()
        if not model:
            return
        if model.violation_count == 0:
            return

        model.violation_count = 0
        model.last_seen_at = datetime.now(UTC)
        self._session.add(model)
        self._session.commit()

    @staticmethod
    def _to_domain(model: SupportUserModel) -> SupportUser:
        return SupportUser(
            user_id=model.user_id,
            display_name=model.display_name,
            is_blocked=model.is_blocked,
            violation_count=model.violation_count,
            blocked_reason=model.blocked_reason,
            blocked_at=model.blocked_at,
            last_seen_at=model.last_seen_at,
        )
