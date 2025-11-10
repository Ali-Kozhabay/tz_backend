import asyncio
from contextlib import suppress
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.security import decode_token
from app.db import session as session_module
from app.models.user import User, UserRole
from app.schemas.chat import MessagePayload
from app.services.chat import ChatBroker, create_message, get_or_create_channel, set_pin, soft_delete_message
from app.services.redis import get_async_redis

router = APIRouter(tags=["chat"])


async def authenticate(websocket: WebSocket) -> User:
    token = websocket.query_params.get("token") or websocket.headers.get("authorization", "").replace("Bearer ", "")
    if not token:
        await websocket.close(code=4401)
        raise WebSocketDisconnect
    payload = decode_token(token)
    if payload.get("type") != "access":
        await websocket.close(code=4401)
        raise WebSocketDisconnect
    async with session_module.SessionLocal() as session:
        user = await session.get(User, int(payload["sub"]))
    if not user:
        await websocket.close(code=4401)
        raise WebSocketDisconnect
    return user


@router.websocket("/ws/channels/{slug}")
async def websocket_endpoint(websocket: WebSocket, slug: str):
    await websocket.accept()
    user = await authenticate(websocket)

    async with session_module.SessionLocal() as session:
        await get_or_create_channel(session, slug)

    redis = get_async_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"channel:{slug}")

    async def reader():
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                await websocket.send_text(message["data"])
        except asyncio.CancelledError:
            pass

    reader_task = asyncio.create_task(reader())
    broker = ChatBroker(redis)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            event_type = data.get("type")
            payload = data.get("payload", {})
            async with session_module.SessionLocal() as session:
                if event_type == "message.create":
                    await create_message(
                        session,
                        broker,
                        user_id=user.id,
                        channel_slug=slug,
                        payload=MessagePayload(**payload),
                    )
                elif event_type == "message.delete":
                    await soft_delete_message(
                        session,
                        broker,
                        message_id=payload["id"],
                        channel_slug=slug,
                    )
                elif event_type == "message.pin":
                    if user.role not in (UserRole.ADMIN,):
                        continue
                    await set_pin(
                        session,
                        broker,
                        message_id=payload["id"],
                        channel_slug=slug,
                        pinned=payload.get("pinned", True),
                    )
    except WebSocketDisconnect:
        reader_task.cancel()
    except Exception:
        reader_task.cancel()
        raise
    finally:
        with suppress(asyncio.CancelledError):
            await reader_task
        await pubsub.unsubscribe(f"channel:{slug}")
        await pubsub.close()
