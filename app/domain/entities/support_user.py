from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SupportUser:
    user_id: str
    display_name: str | None
    is_blocked: bool
    violation_count: int
    blocked_reason: str | None
    blocked_at: datetime | None
    last_seen_at: datetime | None
