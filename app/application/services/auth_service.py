from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError

from app.application.interfaces.auth_user_repository import AuthUserRepository
from app.domain.entities.auth_user import AuthUser


class UserAlreadyExistsError(ValueError):
    pass


@dataclass(slots=True)
class AccessToken:
    token: str
    expires_at: datetime


class AuthService:
    def __init__(
        self,
        user_repository: AuthUserRepository,
        token_secret: str,
        token_ttl_minutes: int = 60,
        token_algorithm: str = "HS256",
        password_iterations: int = 390000,
    ) -> None:
        self._user_repository = user_repository
        self._token_secret = token_secret
        self._token_ttl_minutes = max(1, token_ttl_minutes)
        self._token_algorithm = token_algorithm
        self._password_iterations = max(120000, password_iterations)

    def authenticate_and_issue_token(
        self,
        username: str,
        password: str,
    ) -> tuple[AuthUser, AccessToken] | None:
        user = self.authenticate(username=username, password=password)
        if not user:
            return None
        return user, self.issue_access_token(user)

    def authenticate(self, username: str, password: str) -> AuthUser | None:
        normalized_username = self._normalize_username(username)
        user = self._user_repository.get_by_username(normalized_username)
        if not user or not user.is_active:
            return None
        if not self.verify_password(password=password, encoded_password=user.password_hash):
            return None

        self._user_repository.touch_last_login(normalized_username)
        return self._user_repository.get_by_username(normalized_username)

    def get_active_user(self, username: str) -> AuthUser | None:
        normalized_username = self._normalize_username(username)
        user = self._user_repository.get_by_username(normalized_username)
        if not user or not user.is_active:
            return None
        return user

    def get_user_from_token(self, token: str) -> AuthUser | None:
        try:
            payload = jwt.decode(
                token,
                self._token_secret,
                algorithms=[self._token_algorithm],
                options={"require": ["exp", "iat", "sub"]},
            )
        except InvalidTokenError:
            return None

        subject = payload.get("sub")
        if not isinstance(subject, str):
            return None

        user = self._user_repository.get_by_username(subject)
        if not user or not user.is_active:
            return None
        return user

    def issue_access_token(self, user: AuthUser) -> AccessToken:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self._token_ttl_minutes)
        payload = {
            "sub": user.username,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "is_admin": user.is_admin,
            "token_type": "access",
        }
        token = jwt.encode(payload, self._token_secret, algorithm=self._token_algorithm)
        return AccessToken(token=token, expires_at=expires_at)

    def create_user(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
        is_admin: bool = False,
        is_active: bool = True,
    ) -> AuthUser:
        normalized_username = self._normalize_username(username)
        if self._user_repository.get_by_username(normalized_username):
            raise UserAlreadyExistsError(f"Username '{normalized_username}' already exists.")

        password_hash = self.hash_password(password=password)
        return self._user_repository.create_user(
            username=normalized_username,
            password_hash=password_hash,
            display_name=(display_name.strip() if display_name else None),
            is_admin=is_admin,
            is_active=is_active,
        )

    def ensure_bootstrap_admin(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
    ) -> tuple[AuthUser, bool] | None:
        normalized_username = self._normalize_username(username)
        if not normalized_username or not password.strip():
            return None

        existing_user = self._user_repository.get_by_username(normalized_username)
        if existing_user:
            return existing_user, False

        created = self.create_user(
            username=normalized_username,
            password=password,
            display_name=display_name,
            is_admin=True,
            is_active=True,
        )
        return created, True

    def hash_password(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password_bytes,
            salt,
            self._password_iterations,
        )
        encoded_salt = base64.b64encode(salt).decode("ascii")
        encoded_digest = base64.b64encode(digest).decode("ascii")
        return f"pbkdf2_sha256${self._password_iterations}${encoded_salt}${encoded_digest}"

    @staticmethod
    def verify_password(password: str, encoded_password: str) -> bool:
        try:
            algorithm, iterations_raw, encoded_salt, encoded_digest = encoded_password.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            iterations = int(iterations_raw)
            salt = base64.b64decode(encoded_salt.encode("ascii"))
            expected_digest = base64.b64decode(encoded_digest.encode("ascii"))
        except (ValueError, TypeError):
            return False

        candidate_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=len(expected_digest),
        )
        return hmac.compare_digest(candidate_digest, expected_digest)

    @staticmethod
    def _normalize_username(username: str) -> str:
        return username.strip().lower()
