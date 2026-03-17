from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.application.interfaces.support_user_repository import SupportUserRepository
from app.domain.entities.support_user import SupportUser

ERROR_CODE_PATTERN = re.compile(r"\b(?:ERR|ERROR|HTTP|E)[-_]?\d{3,5}\b", re.IGNORECASE)

TECHNICAL_KEYWORDS = {
    "api",
    "app",
    "auth",
    "backend",
    "base",
    "bug",
    "certificado",
    "conexion",
    "database",
    "deploy",
    "error",
    "falla",
    "http",
    "incidencia",
    "infra",
    "integracion",
    "login",
    "logs",
    "password",
    "postgres",
    "problema",
    "redis",
    "server",
    "servicio",
    "sistema",
    "soporte",
    "sql",
    "ticket",
    "timeout",
    "token",
}

OFF_TOPIC_KEYWORDS = {
    "amor",
    "chiste",
    "futbol",
    "horoscopo",
    "horoscope",
    "musica",
    "pelicula",
    "receta",
    "tarot",
    "zodiac",
}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.lower()


@dataclass(slots=True)
class QueryGuardResult:
    allowed: bool
    blocked: bool
    reason: str | None
    violation_count: int


class UserGuardService:
    def __init__(
        self,
        user_repository: SupportUserRepository,
        violation_threshold: int,
        enabled: bool = True,
    ) -> None:
        self._user_repository = user_repository
        self._violation_threshold = max(1, violation_threshold)
        self._enabled = enabled

    def ensure_user(self, user_id: str, display_name: str | None = None) -> SupportUser:
        return self._user_repository.get_or_create(user_id=user_id, display_name=display_name)

    def evaluate_query(self, user_id: str, query_text: str) -> QueryGuardResult:
        if not self._enabled:
            return QueryGuardResult(allowed=True, blocked=False, reason=None, violation_count=0)

        user = self._user_repository.get_by_user_id(user_id)
        if user and user.is_blocked:
            return QueryGuardResult(
                allowed=False,
                blocked=True,
                reason=user.blocked_reason or "Account is blocked.",
                violation_count=user.violation_count,
            )

        reason = self._classify_query_issue(query_text)
        if not reason:
            return QueryGuardResult(
                allowed=True,
                blocked=False,
                reason=None,
                violation_count=(user.violation_count if user else 0),
            )

        updated_user = self._user_repository.increment_violation(
            user_id=user_id,
            reason=reason,
            threshold=self._violation_threshold,
        )
        return QueryGuardResult(
            allowed=False,
            blocked=updated_user.is_blocked,
            reason=reason,
            violation_count=updated_user.violation_count,
        )

    def mark_success(self, user_id: str) -> None:
        if not self._enabled:
            return
        self._user_repository.reset_violations(user_id)

    def _classify_query_issue(self, query_text: str) -> str | None:
        normalized = _normalize_text(query_text).strip()
        if len(normalized) < 3:
            return "empty_or_too_short_query"

        if any(keyword in normalized for keyword in OFF_TOPIC_KEYWORDS):
            return "off_topic_query"

        if ERROR_CODE_PATTERN.search(query_text):
            return None

        tokens = set(re.findall(r"[a-z0-9_-]{2,50}", normalized))
        if tokens.intersection(TECHNICAL_KEYWORDS):
            return None

        if re.search(r"\d", normalized):
            return None

        return "non_technical_query"
