from typing import Dict
from fastapi import Body, FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uuid
from autogen_chat import AutogenChat
import asyncio
import uvicorn
from dotenv import load_dotenv, find_dotenv
import openai
import os

from websocket_proxy import WebSocketProxy

_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']
# openai.log='debug'

app = FastAPI()
agents: Dict[str, AutogenChat] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[AutogenChat] = []

    async def connect(self, autogen_group_chat: AutogenChat):
        await autogen_group_chat.websocket.accept()
        self.active_connections.append(autogen_group_chat)

    async def disconnect(self, autogen_group_chat: AutogenChat):
        autogen_group_chat.client_receive_queue.put_nowait("DO_FINISH")
        print(f"autogen_group_chat {autogen_group_chat.chat_id} disconnected")
        self.active_connections.remove(autogen_group_chat)


manager = ConnectionManager()


async def send_to_client(autogen_group_chat: AutogenChat):
    """Send message back to the user"""
    while True:
        reply = await autogen_group_chat.client_receive_queue.get()
        if reply and reply == "DO_FINISH":
            autogen_group_chat.client_receive_queue.task_done()
            break
        print(f"Sending to user:", reply)
        await autogen_group_chat.websocket.send_text(reply)
        autogen_group_chat.client_receive_queue.task_done()
        await asyncio.sleep(0.05)

async def receive_from_client(autogen_group_chat: AutogenChat):
    """Receive message from the user"""
    while True:
        data = await autogen_group_chat.websocket.receive_text()
        print(f"Got data from user: ", data)
        if data and data == "DO_FINISH":
            await autogen_group_chat.client_receive_queue.put("DO_FINISH")
            await autogen_group_chat.client_sent_queue.put("DO_FINISH")
            break
        await autogen_group_chat.client_sent_queue.put(data)
        await asyncio.sleep(0.05)

async def create_agent(chat_id: str, message: str) -> AutogenChat:
    autogen_group_chat = None
    try:
        autogen_group_chat = AutogenChat(chat_id=chat_id, websocket=WebSocketProxy())
        await manager.connect(autogen_group_chat)
        data = message
        future_calls = asyncio.gather(autogen_group_chat.start(data), send_to_client(autogen_group_chat), receive_from_client(autogen_group_chat))
        return autogen_group_chat
    except Exception as e:
        print("ERROR", str(e))
        raise


def sanitize_message(message: str) -> str:
    _BRKT = " BRKT"
    if message.endswith(_BRKT):
        message = message[:(-1 * len(_BRKT))]
    return message


@app.post("/chat/{chat_id}")
async def chat(chat_id: str, message: str = Body(..., embed=True)):
    # New Chat
    if chat_id not in agents:
        agent = await create_agent("julius", "Hello!")
        agents[chat_id] = agent
        # Ignore first message
        _ = await agent.websocket.get_message_from_bot()
    else:
        agent = agents[chat_id]

    await agent.websocket.send_message_to_bot(message)
    message = await agent.websocket.get_message_from_bot()
    message = sanitize_message(message)
    return message


@app.delete("/chat/{chat_id}")
async def close_chat(chat_id: str):
    agent = agents.get(chat_id)
    if agent:
        await manager.disconnect(agent)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
