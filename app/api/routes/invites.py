from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User, UserRole
from app.schemas.invite import InviteCreate, InviteRead, InviteRedeemRequest
from app.services.invites import create_invite, redeem_invite

router = APIRouter(tags=["invites"])


@router.post("/admin/invites", response_model=InviteRead, status_code=status.HTTP_201_CREATED)
async def admin_create_invite(
    payload: InviteCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_role(UserRole.ADMIN)),
):
    expires_at = payload.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="expired")
    try:
        role = UserRole(payload.role_to_grant)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid-role") from exc
    invite = await create_invite(
        db,
        role_to_grant=role,
        expires_at=expires_at,
        actor_id=actor.id,
    )
    return InviteRead(code=invite.code)


@router.post("/invites/redeem", response_model=dict)
async def redeem(
    payload: InviteRedeemRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.USER)),
):
    try:
        new_role = await redeem_invite(db, code=payload.code, user=user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"role": new_role.value}
