from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import enforce_rate_limit, get_db
from app.crud import users as users_crud
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenPair, TokenRefreshRequest
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    await enforce_rate_limit(f"register:{user_in.email}", limit=5, window_seconds=3600)

    existing = await users_crud.get_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email-exists")
    try:
        password_hash = get_password_hash(user_in.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    user = await users_crud.create(
        db,
        email=user_in.email,
        password_hash=password_hash,
    )
    return user


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    await enforce_rate_limit(f"login:{body.email}", limit=10, window_seconds=300)
    user = await users_crud.get_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid")

    return TokenPair(
        access=create_access_token(str(user.id)),
        refresh=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: TokenRefreshRequest) -> TokenPair:
    await enforce_rate_limit("refresh", limit=50, window_seconds=60)
    data = decode_token(payload.refresh)
    if data.get("type") != TokenType.REFRESH.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user_id = data["sub"]
    return TokenPair(
        access=create_access_token(str(user_id)),
        refresh=create_refresh_token(str(user_id)),
    )
