from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class MessagePayload(BaseModel):
    text: str = Field(max_length=2000)
    parent_id: Optional[int] = None
    attachments: List[dict] = Field(default_factory=list)


class ChatEvent(BaseModel):
    type: Literal["message.create", "message.delete", "message.pin"]
    payload: dict


class MessageRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    channel_id: int
    user_id: int
    parent_id: Optional[int] = None
    text: str
    attachments: List[Any]
    pinned: bool
    deleted_at: Optional[datetime]
    created_at: datetime
