from __future__ import annotations

from app.application.interfaces.support_user_repository import SupportUserRepository
from app.application.services.user_guard_service import UserGuardService
from app.domain.entities.support_user import SupportUser


class FakeSupportUserRepository(SupportUserRepository):
    def __init__(self) -> None:
        self.users: dict[str, SupportUser] = {}

    def get_or_create(self, user_id: str, display_name: str | None = None) -> SupportUser:
        user = self.users.get(user_id)
        if user:
            return user
        user = SupportUser(
            user_id=user_id,
            display_name=display_name,
            is_blocked=False,
            violation_count=0,
            blocked_reason=None,
            blocked_at=None,
            last_seen_at=None,
        )
        self.users[user_id] = user
        return user

    def get_by_user_id(self, user_id: str) -> SupportUser | None:
        return self.users.get(user_id)

    def increment_violation(self, user_id: str, reason: str, threshold: int) -> SupportUser:
        user = self.get_or_create(user_id)
        user.violation_count += 1
        if user.violation_count >= threshold:
            user.is_blocked = True
            user.blocked_reason = reason
        return user

    def reset_violations(self, user_id: str) -> None:
        user = self.users.get(user_id)
        if not user:
            return
        user.violation_count = 0


def test_guard_allows_technical_query() -> None:
    repository = FakeSupportUserRepository()
    guard = UserGuardService(repository, violation_threshold=3, enabled=True)
    guard.ensure_user("u1")

    result = guard.evaluate_query("u1", "ERR-401 on login in auth API")

    assert result.allowed is True
    assert result.blocked is False


def test_guard_blocks_after_repeated_off_topic_queries() -> None:
    repository = FakeSupportUserRepository()
    guard = UserGuardService(repository, violation_threshold=3, enabled=True)
    guard.ensure_user("u2")

    guard.evaluate_query("u2", "horoscopo de hoy")
    guard.evaluate_query("u2", "horoscopo de hoy")
    final = guard.evaluate_query("u2", "horoscopo de hoy")

    assert final.allowed is False
    assert final.blocked is True
    assert final.violation_count == 3


def test_guard_rejects_blank_or_spaces_queries() -> None:
    repository = FakeSupportUserRepository()
    guard = UserGuardService(repository, violation_threshold=3, enabled=True)
    guard.ensure_user("u3")

    result = guard.evaluate_query("u3", "   ")

    assert result.allowed is False
    assert result.reason == "empty_or_too_short_query"
