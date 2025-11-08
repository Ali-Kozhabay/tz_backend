from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def _create_token(sub: str, token_type: TokenType, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": sub,
        "type": token_type.value,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_access_token(sub: str) -> str:
    settings = get_settings()
    return _create_token(
        sub=sub,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_ttl_minutes),
    )


def create_refresh_token(sub: str) -> str:
    settings = get_settings()
    return _create_token(
        sub=sub,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_ttl_days),
    )


def decode_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)
