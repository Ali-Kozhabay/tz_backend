from datetime import datetime, timezone
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invite import Invite
from app.models.user import User, UserRole
from app.services.audit import log_event


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def create_invite(
    db: AsyncSession,
    *,
    role_to_grant: UserRole,
    expires_at: datetime,
    actor_id: int,
) -> Invite:
    code = secrets.token_urlsafe(8)
    expires_at = _ensure_aware(expires_at)
    invite = Invite(
        code=code,
        role_to_grant=role_to_grant.value,
        expires_at=expires_at,
    )
    db.add(invite)
    await log_event(
        db,
        actor_id=actor_id,
        action="invite.create",
        entity="invite",
        entity_id=code,
        meta={"role": role_to_grant.value},
    )
    await db.commit()
    await db.refresh(invite)
    return invite


async def redeem_invite(db: AsyncSession, *, code: str, user: User) -> UserRole:
    invite = await db.get(Invite, code)
    if invite is None:
        raise ValueError("invalid-code")
    if invite.used_by is not None:
        raise ValueError("invite-used")
    expires_at = _ensure_aware(invite.expires_at)
    if expires_at <= datetime.now(timezone.utc):
        raise ValueError("invite-expired")

    user.role = UserRole(invite.role_to_grant)
    invite.used_by = user.id
    db.add_all([user, invite])
    await log_event(
        db,
        actor_id=user.id,
        action="invite.redeem",
        entity="invite",
        entity_id=invite.code,
        meta={"role": user.role.value},
    )
    await db.commit()
    return user.role
