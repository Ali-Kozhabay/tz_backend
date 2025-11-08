import os
import tempfile
from collections.abc import AsyncIterator, Awaitable, Callable

import fakeredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import config as config_module
from app.core.security import get_password_hash
from app.db import session as session_module
from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.user import User, UserRole
from app.services import redis as redis_service


@pytest_asyncio.fixture(scope="session", autouse=True)
async def configure_test_db() -> AsyncIterator[None]:
    tmpdir = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmpdir}/test.db"
    config_module.get_settings.cache_clear()
    session_module.reset_engine()
    async with session_module.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    fake_sync = fakeredis.FakeRedis(decode_responses=True)
    fake_async = fakeredis.aioredis.FakeRedis(decode_responses=True)
    redis_service.override_redis(fake_sync, fake_async)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_module.SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    async with session_module.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with session_module.SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def user_factory(db_session: AsyncSession) -> AsyncIterator[Callable[[str, str, UserRole], Awaitable[User]]]:
    async def factory(email: str, password: str, role: UserRole = UserRole.USER) -> User:
        user = User(email=email, password_hash=get_password_hash(password), role=role)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    yield factory
