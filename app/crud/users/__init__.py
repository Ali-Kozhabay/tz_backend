from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.user import User, UserRole


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    res = await db.execute(select(User).where(User.email == email))
    return res.scalar()


async def create(
    db: AsyncSession,
    *,
    email: str,
    password_hash: str,
    role: UserRole = UserRole.USER,
) -> User:
    user = User(email=email, password_hash=password_hash, role=role)
    profile = Profile(user=user)
    db.add_all([user, profile])
    await db.commit()
    await db.refresh(user)
    return user
