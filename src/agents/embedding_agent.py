import os
import sys
import pickle
from agents.base_agent import BaseAgent

class EmbeddingAgent(BaseAgent):
    def __init__(self, name, system, embedding_fn):
        super().__init__(name, system)
        self.embedding_fn = embedding_fn
        # Declarar vectores del embedding y asignarlos
        with open("src/embedding/embeddings.pkl", 'rb') as f:
            self.data = pickle.load(f)

    async def handle(self, message):
        query = message["content"]["query"]
        # Preprocesar la query
        results = self.embedding_fn(query, self.data)
        await self.send("validator", {"source": "embedding", "results": results})