from datetime import datetime

from pydantic import BaseModel, Field


class InviteCreate(BaseModel):
    role_to_grant: str
    expires_at: datetime


class InviteRedeemRequest(BaseModel):
    code: str = Field(min_length=6)


class InviteRead(BaseModel):
    code: str
