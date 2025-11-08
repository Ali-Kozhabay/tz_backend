from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.api.deps import require_role
from app.models.user import User, UserRole
from app.schemas.storage import SignedUrlResponse
from app.services.storage import generate_presigned_url

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/sign", response_model=SignedUrlResponse)
async def sign_url(
    key: str = Query(..., min_length=1),
    _: User = Depends(require_role(UserRole.USER)),
):
    try:
        url = await run_in_threadpool(generate_presigned_url, key, timedelta(minutes=5))
    except Exception as exc:  # pragma: no cover - minio-specific
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SignedUrlResponse(url=url)
