import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import User

COOKIE_NAME = "access_token"
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (Argon2Error, InvalidHashError):
        return False


def create_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.jwt_secret, algorithm="HS256")


def set_auth_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.jwt_expire_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "No has iniciado sesión")
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise unauthorized
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los administradores pueden hacer esto")
    return user


async def seed_admin(session: AsyncSession) -> None:
    """Create the first admin from .env when the users table is empty."""
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return
    if await session.scalar(select(func.count()).select_from(User)):
        return
    session.add(
        User(
            email=settings.admin_email.strip().lower(),
            name=settings.admin_name,
            password_hash=hash_password(settings.admin_password),
            role="admin",
        )
    )
    await session.commit()
