class AgentSystem:
    """
    Clase que representa un sistema al que pertenecen agentes los cuales pueden enviar mensajes entre ellos.
    """
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent):
        """
        Registrar al agente en el sistema.
        """
        self.agents[agent.name] = agent

    async def send_message(self, from_agent, to_agent, content):
        """
        Enviar un mensaje desde un agente a otro.
        """
        if to_agent in self.agents:
            await self.agents[to_agent].inbox.put({
                "from": from_agent,
                "to": to_agent,
                "content": content
            })
        else:
            print(f"[System] Agente destino '{to_agent}' no registrado.")