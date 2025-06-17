import asyncio

class BaseAgent:
    """
    Clase base para todos los agentes del sistema multiagente.

    Proporciona funcionalidades comunes como el manejo de mensajes, 
    acceso al sistema compartido y métodos para enviar y recibir información 
    de otros agentes. Esta clase debe ser extendida por agentes específicos 
    como coordinadores, validadores, recolectores, etc.

    Atributos:
        name (str): Nombre único del agente dentro del sistema.
        system (System): Referencia al sistema multiagente, que provee el entorno
                         de comunicación entre agentes.

    Métodos:
        handle(message): Método que debe ser sobrescrito por agentes hijos para 
                         definir cómo manejar un mensaje entrante.
        send(receiver, content): Envia un mensaje asincrónico a otro agente.
        receive(): Espera y recibe un mensaje dirigido a este agente.
    """
    
    def __init__(self, name, system):
        """
        Inicializa el agente.

        Args:
            name (str): Nombre del agente.
            system (System): Referencia al sistema multiagente.
        """
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