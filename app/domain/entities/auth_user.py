from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AuthUser:
    username: str
    display_name: str | None
    password_hash: str
    is_active: bool
    is_admin: bool
    last_login_at: datetime | None
