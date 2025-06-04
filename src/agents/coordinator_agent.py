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

        cocktails = data.get("cocktails", [])
        search_type = data.get("make_search", "ontology")

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
        payload_embedding = {"query": query}

        # Enviar a los agentes correspondientes
        if "ontology" in search_type:
            await self.send("ontology", payload_ontology)

        if "embedding" in search_type:
            await self.send("embedding", payload_embedding)


        # El KnowledgeAgent será el encargado de combinar respuestas