from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_invite_flow(client, user_factory, db_session: AsyncSession):
    admin = await user_factory("admin@example.com", "password123", role=UserRole.ADMIN)
    user = await user_factory("member@example.com", "password123", role=UserRole.USER)

    admin_token = create_access_token(str(admin.id))
    expires = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    res = await client.post(
        "/admin/invites",
        json={"role_to_grant": "member", "expires_at": expires},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201
    code = res.json()["code"]

    user_token = create_access_token(str(user.id))
    res = await client.post(
        "/invites/redeem",
        json={"code": code},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert res.status_code == 200
    await db_session.refresh(user)
    assert user.role == UserRole.MEMBER
