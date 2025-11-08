from datetime import timedelta

from minio import Minio

from app.core.config import get_settings

_client: Minio | None = None


def get_client() -> Minio:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Minio(
            settings.s3_endpoint.replace("http://", "").replace("https://", ""),
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            secure=settings.s3_endpoint.startswith("https"),
        )
    return _client


def generate_presigned_url(key: str, expires: timedelta = timedelta(minutes=5)) -> str:
    client = get_client()
    settings = get_settings()
    return client.get_presigned_url(
        "GET",
        bucket_name=settings.s3_bucket,
        object_name=key,
        expires=expires,
    )
