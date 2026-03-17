from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.dependencies import ChatUserContext, get_auth_service, require_admin_user
from app.application.services.auth_service import AccessToken, UserAlreadyExistsError
from app.domain.entities.auth_user import AuthUser
from app.main import app


class FakeAuthServiceLoginOk:
    def authenticate_and_issue_token(
        self,
        username: str,
        password: str,
    ) -> tuple[AuthUser, AccessToken] | None:
        user = AuthUser(
            username=username,
            display_name="Demo User",
            password_hash="hashed",
            is_active=True,
            is_admin=False,
            last_login_at=datetime.now(UTC),
        )
        token = AccessToken(
            token="fake-token",
            expires_at=datetime.now(UTC) + timedelta(minutes=60),
        )
        return user, token


class FakeAuthServiceLoginFail:
    def authenticate_and_issue_token(
        self,
        username: str,
        password: str,
    ) -> tuple[AuthUser, AccessToken] | None:
        return None


class FakeAuthServiceCreateOk:
    def create_user(  # type: ignore[no-untyped-def]
        self,
        username,
        password,
        display_name=None,
        is_active=True,
        is_admin=False,
    ) -> AuthUser:
        return AuthUser(
            username=username,
            display_name=display_name,
            password_hash="hashed",
            is_active=is_active,
            is_admin=is_admin,
            last_login_at=None,
        )


class FakeAuthServiceCreateConflict:
    def create_user(  # type: ignore[no-untyped-def]
        self,
        username,
        password,
        display_name=None,
        is_active=True,
        is_admin=False,
    ) -> AuthUser:
        raise UserAlreadyExistsError(f"Username '{username}' already exists.")


def test_auth_login_returns_access_token() -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthServiceLoginOk()
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "maria.romero", "password": "my-strong-pass"},
    )
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert payload["access_token"] == "fake-token"
    assert payload["token_type"] == "bearer"
    assert payload["user"]["username"] == "maria.romero"


def test_auth_login_rejects_invalid_credentials() -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthServiceLoginFail()
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "maria.romero", "password": "wrong-pass"},
    )
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert payload["code"] == "invalid_credentials"


def test_auth_create_user_returns_created_user() -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthServiceCreateOk()
    app.dependency_overrides[require_admin_user] = lambda: ChatUserContext(
        user_id="admin",
        display_name="Admin",
        is_admin=True,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/users",
        json={
            "username": "new.user",
            "password": "my-strong-pass",
            "display_name": "New User",
            "is_active": True,
            "is_admin": False,
        },
    )
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert payload["username"] == "new.user"
    assert payload["display_name"] == "New User"
    assert payload["is_admin"] is False


def test_auth_create_user_conflict_returns_standard_error() -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthServiceCreateConflict()
    app.dependency_overrides[require_admin_user] = lambda: ChatUserContext(
        user_id="admin",
        display_name="Admin",
        is_admin=True,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/users",
        json={
            "username": "new.user",
            "password": "my-strong-pass",
        },
    )
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 409
    assert payload["code"] == "user_already_exists"
