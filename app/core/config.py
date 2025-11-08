from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.engine import make_url


class Settings(BaseModel):
    """Application configuration derived from environment variables."""

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    jwt_secret: str = Field(default="changeme")
    jwt_alg: str = Field(default="HS256")
    access_token_ttl_minutes: int = Field(default=15)
    refresh_token_ttl_days: int = Field(default=7)
    smtp_host: str = Field(default="localhost")
    smtp_port: int = Field(default=1025)
    smtp_user: str | None = Field(default=None)
    smtp_pass: str | None = Field(default=None)
    s3_endpoint: str = Field(default="http://localhost:9000")
    s3_access_key: str = Field(default="minio")
    s3_secret_key: str = Field(default="minio123")
    s3_bucket: str = Field(default="courses")
    base_url: str = Field(default="http://localhost:8000")
    environment: Literal["development", "production", "test"] = Field(
        default="development"
    )

    class Config:
        env_file = ".env"
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
