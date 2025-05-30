import asyncio

class BaseAgent:
    def __init__(self, name, system):
        self.name = name
        self.system = system
        self.inbox = asyncio.Queue()

    async def send(self, to_agent, content):
        await self.system.send_message(self.name, to_agent, content)

    async def receive(self):
        return await self.inbox.get()

    async def run(self):
        while True:
            message = await self.receive()
            await self.handle(message)

    async def handle(self, message):
        raise NotImplementedError(f"{self.name} no implementó handle()")