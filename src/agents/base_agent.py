import asyncio

class BaseAgent:
    """
    Clase que representa a un agente.
    """
    def __init__(self, name, system):
        self.name = name
        self.system = system
        self.inbox = asyncio.Queue()

    async def send(self, to_agent, content):
        """
        Envía un mensaje a otro agente.
        """
        await self.system.send_message(self.name, to_agent, content)

    async def receive(self):
        """
        Recibe un mensaje de otro agente.
        """
        return await self.inbox.get()

    async def run(self):
        """
        Ejecuta la funcionalidad de un agente tras recibir el mensaje esperado.
        """
        while True:
            message = await self.receive()
            await self.handle(message)

    async def handle(self, message):
        """
        Ejecuta la funcionalidad de un agente. Debe ser implementada en la definición de un agente.
        """
        raise NotImplementedError(f"{self.name} no implementó handle()")