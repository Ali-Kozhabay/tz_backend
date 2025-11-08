from datetime import timedelta

import pytest

from app.core.security import create_access_token
from app.services import storage as storage_service


class DummyMinio:
    def __init__(self):
        self.calls = []

    def get_presigned_url(self, method, bucket_name, object_name, expires):
        self.calls.append((method, bucket_name, object_name, expires))
        return f"https://example.com/{object_name}?token=fake"


@pytest.mark.asyncio
async def test_signed_url_generation(client, user_factory, monkeypatch):
    user = await user_factory("files@example.com", "password123")
    token = create_access_token(str(user.id))
    dummy = DummyMinio()
    monkeypatch.setattr(storage_service, "_client", dummy)

    res = await client.get(
        "/storage/sign",
        params={"key": "lesson/video.mp4"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["url"].startswith("https://example.com")
    assert dummy.calls
    _, _, key, expires = dummy.calls[0]
    assert key == "lesson/video.mp4"
    assert isinstance(expires, timedelta)
