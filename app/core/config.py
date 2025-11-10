import os
from functools import lru_cache
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy.engine import make_url


load_dotenv()


def _env_field(name: str, default: Any) -> Field:
    """Return a Field whose default pulls from env vars (fallback to provided default)."""

    return Field(default_factory=lambda name=name, default=default: os.getenv(name, default))


class Settings(BaseModel):
    """Application configuration derived from environment variables."""

    database_url: str = _env_field(
        "DATABASE_URL", "postgresql+asyncpg://superuser:postgres@localhost:5432/app"
    )
    redis_url: str = _env_field("REDIS_URL", "redis://localhost:6379")
    jwt_secret: str = _env_field("JWT_SECRET", "changeme")
    jwt_alg: str = _env_field("JWT_ALG", "HS256")
    access_token_ttl_minutes: int = _env_field("ACCESS_TOKEN_TTL_MINUTES", "15")
    refresh_token_ttl_days: int = _env_field("REFRESH_TOKEN_TTL_DAYS", "7")
    smtp_host: str = _env_field("SMTP_HOST", "localhost")
    smtp_port: int = _env_field("SMTP_PORT", "1025")
    smtp_user: str | None = _env_field("SMTP_USER", None)
    smtp_pass: str | None = _env_field("SMTP_PASS", None)
    s3_endpoint: str = _env_field("S3_ENDPOINT", "http://localhost:9000")
    s3_access_key: str = _env_field("S3_ACCESS_KEY", "minio")
    s3_secret_key: str = _env_field("S3_SECRET_KEY", "minio123")
    s3_bucket: str = _env_field("S3_BUCKET", "courses")
    base_url: str = _env_field("BASE_URL", "http://localhost:8000")
    environment: Literal["development", "production", "test"] = _env_field(
        "ENVIRONMENT", "development"
    )

    class Config:
        env_prefix = ""
        frozen = True

    @property
    def sync_database_url(self) -> str:
        """Return sync driver variant (used by Alembic)."""

        url = make_url(self.database_url)
        driver = url.drivername
        if driver.endswith("+asyncpg"):
            driver = driver.replace("+asyncpg", "+psycopg2")
        elif driver.endswith("+aiosqlite"):
            driver = "sqlite"
        url = url.set(drivername=driver)
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()  # type: ignore[arg-type]
