from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def _create_engine() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False, future=True
    )
    return engine, session_factory


engine, SessionLocal = _create_engine()


def reset_engine() -> None:
    """Recreate engine + session factory (useful for tests)."""

    global engine, SessionLocal
    engine.sync_engine.dispose()
    engine, SessionLocal = _create_engine()
