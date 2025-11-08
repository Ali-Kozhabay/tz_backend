import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_chat_message_lifecycle(user_factory):
    user = await user_factory("chat@example.com", "password123", role=UserRole.MEMBER)
    token = create_access_token(str(user.id))
    message = {
        "type": "message.create",
        "payload": {"text": "hi there", "parent_id": None, "attachments": []},
    }

    def websocket_flow():
        with TestClient(app) as sync_client:
            with sync_client.websocket_connect(f"/ws/channels/hq?token={token}") as ws:
                ws.send_text(json.dumps(message))
                event = ws.receive_text()
                return json.loads(event)

    data = await asyncio.to_thread(websocket_flow)
    assert data["type"] == "message.created"
    assert data["payload"]["text"] == "hi there"
