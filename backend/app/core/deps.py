"""Shared FastAPI dependencies: DB session, current user, RBAC guards."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db.models.user import User, UserRole
from app.db.session import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> User:
    if token is None:
        raise _CREDENTIALS_EXCEPTION

    try:
        payload = decode_token(token, expected_type=TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise _CREDENTIALS_EXCEPTION from exc

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise _CREDENTIALS_EXCEPTION from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXCEPTION
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable[[CurrentUser], User]:
    """RBAC dependency factory: restricts a route to the given roles.

    Usage: `current_user: User = Depends(require_roles(UserRole.LECTURER, UserRole.ADMIN))`
    """

    def _guard(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _guard


async def get_user_by_email(
    db: AsyncSession, email: str, roles: Sequence[UserRole] | None = None
) -> User | None:
    query = select(User).where(User.email == email)
    if roles:
        query = query.where(User.role.in_(roles))
    result = await db.execute(query)
    return result.scalar_one_or_none()
