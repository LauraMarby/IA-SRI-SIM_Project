import json
import re
from agents.base_agent import BaseAgent

class CoordinatorAgent(BaseAgent):
    async def handle(self, message):
        content = message["content"]

        # Limpiar formato tipo Markdown si viene con ```
        cleaned = re.sub(r"```(?:json)?\n?", "", content.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```", "", cleaned.strip())

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[Coordinator] JSON inválido: {e}")
            return
    
        query = data.get("translated_prompt", "unknown query")
        embedding_query = data.get("embedding_query", "unnecesary question")

        cocktails = data.get("cocktails", [])

        if not cocktails:
            print("[Coordinator] No se detectaron cócteles.")

        # Preparar listas para el payload conjunto
        cocktail_names = []
        field_sets = []

        for cocktail in cocktails:
            nombre = cocktail.get("name")
            campos = cocktail.get("fields_requested", [])

            if not nombre or not isinstance(campos, list):
                print(f"[Coordinator] Datos incompletos para un cóctel: {cocktail}")
                continue

            cocktail_names.append(nombre)
            field_sets.append(campos)

        # Construir payload común
        payload_ontology = {"cocktails": cocktail_names, "fields": field_sets}
        payload_embedding = {"query": embedding_query}

        expected_sources = ["ontology", "embedding"]
        # flavors = data.get("flavor_of_drink", [])
        # if flavors is not []:
        #     expected_sources.append("flavors agent")
        #     await self.send("flavors agent", {"cocktails": poner cocteles a averiguar sabor, "flavors": poner sabores buscados en cocteles})

        # Avisar al validador de qué fuentes esperar
        if expected_sources:
            await self.send("validator", {
                "type": "expectation",
                "sources": expected_sources,
                "query": query  # útil para que el validador sepa qué validar
            })


        await self.send("ontology", payload_ontology)
        await self.send("embedding", payload_embedding)
        
