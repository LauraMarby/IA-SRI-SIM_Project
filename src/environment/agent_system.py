class AgentSystem:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent):
        self.agents[agent.name] = agent

    async def send_message(self, from_agent, to_agent, content):
        if to_agent in self.agents:
            await self.agents[to_agent].inbox.put({
                "from": from_agent,
                "to": to_agent,
                "content": content
            })
        else:
            print(f"[System] Agente destino '{to_agent}' no registrado.")