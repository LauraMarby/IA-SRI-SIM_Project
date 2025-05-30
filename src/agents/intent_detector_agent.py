from agents.base_agent import BaseAgent
import google.generativeai as genai

class IntentDetectorAgent(BaseAgent):
    def __init__(self, name, system, model):
        super().__init__(name, system)
        self.model = model

    async def run(self):
        while True:
            msg = await self.receive()
            query = msg["content"]
            sender = msg["from"]

            intent_json = await self.detect_intent(query)

            await self.send(sender, intent_json)

    async def detect_intent(self, query):
        CAMPOS_TRAGO = [
            "Url", "Glass", "Ingredients", "Instructions",
            "Review", "History", "Nutrition", "Alcohol_Content", "Garnish"
        ]

        prompt = f"""
Eres un asistente para preprocesar consultas de usuarios sobre cócteles.

Dada esta consulta: ```{query}```

Responde en JSON con las siguientes claves:

- "original_language": el idioma original del usuario.
- "translated_prompt": la traducción al inglés de la consulta.
- "cocktail_mentioned": true o false.
- "cocktails": una lista con un objeto por cada cóctel mencionado. Cada objeto debe tener:
  - "name": nombre del cóctel.
  - "fields_requested": una lista de 9 valores booleanos, uno por cada campo del cóctel (en este orden: {', '.join(CAMPOS_TRAGO)}). Pon `true` si el usuario quiere saber sobre ese campo, `false` en caso contrario.
- "make_search": debe ser uno de estos valores: "ontology", "embedding", "both", según el tipo de búsqueda necesario.

"""

        response = await self.model.generate_content_async(prompt)
        return response.text