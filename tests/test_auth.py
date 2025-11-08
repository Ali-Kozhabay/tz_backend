import pytest

from app.core.security import decode_token


@pytest.mark.asyncio
async def test_register_login_refresh(client):
    payload = {"email": "user@example.com", "password": "supersecret"}
    res = await client.post("/auth/register", json=payload)
    assert res.status_code == 201

    res = await client.post("/auth/login", json=payload)
    assert res.status_code == 200
    tokens = res.json()
    assert "access" in tokens and "refresh" in tokens
    access_payload = decode_token(tokens["access"])
    assert access_payload["type"] == "access"

    res = await client.post("/auth/refresh", json={"refresh": tokens["refresh"]})
    assert res.status_code == 200
