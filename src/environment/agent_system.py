class AgentSystem:
    """
    Clase que representa el sistema central de coordinación entre agentes.

    Este sistema actúa como un entorno compartido en el que múltiples agentes
    pueden registrarse y enviarse mensajes entre sí de manera asincrónica.
    Permite una arquitectura desacoplada, donde los agentes se comunican
    mediante colas internas sin conocerse directamente.

    Atributos:
        agents (dict): Diccionario que mapea el nombre de cada agente a su instancia correspondiente.
    """

    def __init__(self):
        """
        Inicializa el sistema con un diccionario vacío de agentes registrados.
        """

        self.agents = {}

    def register_agent(self, agent):
        """
        Registra un agente en el sistema, permitiéndole participar en la red de mensajes.

        Parámetros:
            agent (BaseAgent): Instancia del agente que se desea registrar.
                               Debe tener un atributo `name` único y una `inbox` para mensajes.
        """

        self.agents[agent.name] = agent

    async def send_message(self, from_agent, to_agent, content):
        """
        Envía un mensaje desde un agente emisor a un agente receptor registrado.

        Parámetros:
            from_agent (str): Nombre del agente que envía el mensaje.
            to_agent (str): Nombre del agente destinatario.
            content (any): Contenido del mensaje a enviar. Puede ser texto, un objeto, etc.

        Comportamiento:
            - Si el agente de destino está registrado, el mensaje se coloca en su `inbox`.
            - Si el agente de destino no existe, se muestra un mensaje de error por consola.
        """
        
        if to_agent in self.agents:
            await self.agents[to_agent].inbox.put({
                "from": from_agent,
                "to": to_agent,
                "content": content
            })
        else:
            print(f"[System] Agente destino '{to_agent}' no registrado.")