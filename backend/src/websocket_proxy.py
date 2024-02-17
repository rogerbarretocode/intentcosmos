from autogen.agentchat.conversable_agent import asyncio


class WebSocketProxy:
    """Custom class that mimic websocket communication using 2 asyncio.Queue instances."""
    def __init__(self):
        self.in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()

    async def accept(self):
        pass # no-op

    async def send_text(self, message):
        await self.in_queue.put(message)

    async def receive_text(self):
        message = await self.out_queue.get()
        self.out_queue.task_done()
        return message


    async def get_message_from_bot(self):
        message = await self.in_queue.get()
        self.in_queue.task_done()
        return message

    async def send_message_to_bot(self, message):
        await self.out_queue.put(message)

