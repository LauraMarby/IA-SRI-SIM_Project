import json
import re
from agents.base_agent import BaseAgent

class CoordinatorAgent(BaseAgent):
    def __init__(self, name, system, model):
        super().__init__(name, system)
        self.model = model
        self.lang = "en"
        self.query = "Empty query"

    async def handle(self, message):

        sender = message["from"]
        if sender == "user":
    
            content = message["content"]

            # Limpiar formato tipo Markdown si viene con ```
            cleaned = re.sub(r"```(?:json)?\n?", "", content.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"\n?```", "", cleaned.strip())

            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                print(f"[Coordinator] JSON inválido: {e}")
                return
        
            self.query = data.get("translated_prompt", "unknown query")
            embedding_query = data.get("embedding_query", "unnecesary question")
            self.lang = data.get("original_language", "en")

            cocktails = data.get("cocktails", [])

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
                    "query": self.query  # útil para que el validador sepa qué validar
                })


            await self.send("ontology", payload_ontology)
            await self.send("embedding", payload_embedding)
            
        elif sender=="validator":
            content = message["content"]["suficiencia"]
            suficiente = content["suficiente"]
            if suficiente == 'true':
                respuesta = content["first answer"]
                complementos = content["add-ons"]
                razonamiento = content["razonamiento"]

                # Enviando respuesta
                await self.send_response(respuesta, complementos, razonamiento)

                # Limpiando memoria
                self.lang = "en"
                self.query = "Empty query"
                
            else:
                pass

    async def send_response(self, respuesta, complementos, razonamiento):
        # Construir el prompt en base a la query original, la respuesta seleccionada, 
        # los complementos útiles y el razonamiento aplicado.
        prompt = f"""
    You are an expert bartender assistant.
    Answer the following user query in a clear, helpful, and friendly way
    Query: "{self.query}"
    You previously selected the following answer as most relevant:
    \"\"\"{respuesta}\"\"\"
    Additional helpful data:
    \"\"\"{complementos}\"\"\"
    The reasoning used to choose this answer:
    \"\"\"{razonamiento}\"\"\"
    Now, write a final answer in {self.lang.upper()} to send to the user, using the selected data and reasoning. Do not mention that it came from a model or that it was selected. Just provide the final, helpful answer.
    """

        try:
            # Enviar el prompt al modelo (asumiendo método generate)
            output = await self.model.generate_content_async(prompt)

            # Extraer texto limpio
            final_answer = output.text.strip() if hasattr(output, 'text') else str(output).strip()

            # Enviar la respuesta al UserAgent (simulado aquí con un print, reemplaza con tu entorno de mensajes)
            await self.send("user", {
                "type": "respuesta_final",
                "content": final_answer
            })

        except Exception as e:
            await self.send("user", {
                "type": "respuesta_final",
                "content": f"Sorry, I was unable to generate a final answer due to an internal error: {str(e)}"
            })

