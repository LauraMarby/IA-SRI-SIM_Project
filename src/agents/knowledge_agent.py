from .base_agent import BaseAgent

class KnowledgeAgent(BaseAgent):
    async def handle(self, message):
        print(f"[KnowledgeAgent] Recibido de {message['from']}: {message['content']}")
