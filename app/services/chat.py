from datetime import datetime
import json

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Channel, Message
from app.schemas.chat import MessagePayload


class ChatBroker:
    def __init__(self, redis_client: AsyncRedis):
        self.redis = redis_client

    async def publish(self, channel_slug: str, event: str, payload: dict) -> None:
        message = {"type": event, "payload": payload}
        await self.redis.publish(f"channel:{channel_slug}", json.dumps(message))


async def get_or_create_channel(db: AsyncSession, slug: str) -> Channel:
    stmt = select(Channel).where(Channel.slug == slug)
    channel = await db.scalar(stmt)
    if channel:
        return channel

    channel = Channel(slug=slug, is_readonly=slug == "announcements")
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


async def create_message(
    db: AsyncSession,
    broker: ChatBroker,
    *,
    user_id: int,
    channel_slug: str,
    payload: MessagePayload,
) -> Message:
    channel = await get_or_create_channel(db, channel_slug)
    if channel.is_readonly:
        raise PermissionError("channel-readonly")

    message = Message(
        channel_id=channel.id,
        user_id=user_id,
        parent_id=payload.parent_id,
        text=payload.text,
        attachments=payload.attachments,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    await broker.publish(
        channel_slug,
        "message.created",
        {
            "id": message.id,
            "text": message.text,
            "user_id": message.user_id,
            "channel_id": message.channel_id,
        },
    )
    return message


async def soft_delete_message(
    db: AsyncSession,
    broker: ChatBroker,
    *,
    message_id: int,
    channel_slug: str,
) -> None:
    message = await db.get(Message, message_id)
    if not message:
        raise ValueError("message-missing")
    message.deleted_at = datetime.utcnow()
    db.add(message)
    await db.commit()
    await broker.publish(
        channel_slug,
        "message.deleted",
        {"id": message.id},
    )


async def set_pin(
    db: AsyncSession,
    broker: ChatBroker,
    *,
    message_id: int,
    channel_slug: str,
    pinned: bool,
) -> None:
    message = await db.get(Message, message_id)
    if not message:
        raise ValueError("message-missing")
    message.pinned = pinned
    db.add(message)
    await db.commit()
    await broker.publish(
        channel_slug,
        "message.pinned",
        {"id": message.id, "pinned": pinned},
    )
