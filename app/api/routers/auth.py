from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    ChatUserContext,
    get_auth_service,
    require_admin_user,
    require_api_key,
    require_chat_user,
)
from app.application.services.auth_service import AuthService, UserAlreadyExistsError
from app.domain.entities.auth_user import AuthUser
from app.schemas.auth import AuthUserCreateRequest, AuthUserResponse, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(require_api_key)])


def _to_auth_user_response(user: AuthUser) -> AuthUserResponse:
    return AuthUserResponse(
        username=user.username,
        display_name=user.display_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        last_login_at=user.last_login_at,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    result = auth_service.authenticate_and_issue_token(
        username=payload.username,
        password=payload.password,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_credentials",
                "message": "Invalid username or password.",
            },
        )

    user, access_token = result
    return LoginResponse(
        access_token=access_token.token,
        expires_at=access_token.expires_at,
        user=_to_auth_user_response(user),
    )


@router.get("/me", response_model=AuthUserResponse)
def me(
    user_context: Annotated[ChatUserContext, Depends(require_chat_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthUserResponse:
    user = auth_service.get_active_user(user_context.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_or_expired_token",
                "message": "The access token is invalid or expired.",
            },
        )

    return _to_auth_user_response(user)


@router.post(
    "/users",
    response_model=AuthUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: AuthUserCreateRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    _admin: Annotated[ChatUserContext, Depends(require_admin_user)],
) -> AuthUserResponse:
    try:
        user = auth_service.create_user(
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
            is_active=payload.is_active,
            is_admin=payload.is_admin,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "user_already_exists",
                "message": str(exc),
            },
        ) from exc

    return _to_auth_user_response(user)
