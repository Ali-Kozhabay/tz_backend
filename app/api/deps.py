from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenType, decode_token
from app.db.deps import get_db
from app.models.user import User, UserRole
from app.services.redis import get_async_redis
from app.utils.rate_limit import RateLimiter

auth_scheme = HTTPBearer(auto_error=False)
_role_priority = {
    UserRole.GUEST: 0,
    UserRole.USER: 1,
    UserRole.MEMBER: 2,
    UserRole.ADMIN: 3,
}


def get_rate_limiter() -> RateLimiter:
    redis_conn = get_async_redis()
    return RateLimiter(redis_conn)


async def enforce_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    limiter = get_rate_limiter()
    result = await limiter.check(key, limit, window_seconds)
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"retry_after": window_seconds, "remaining": result.remaining},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    payload = decode_token(credentials.credentials)
    if payload.get("type") != TokenType.ACCESS.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = await db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    if payload.get("type") != TokenType.ACCESS.value:
        return None
    return await db.get(User, int(payload["sub"]))


def require_role(min_role: UserRole):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if _role_priority[user.role] < _role_priority[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return user

    return dependency
