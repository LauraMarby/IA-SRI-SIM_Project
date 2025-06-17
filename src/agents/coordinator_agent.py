import json
import re
from agents.base_agent import BaseAgent

class CoordinatorAgent(BaseAgent):
    def __init__(self, name, system, model):
        super().__init__(name, system)
        self.model = model
        self.lang = "en"
        self.query = "Empty query"
        self.embedding_query = []

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
            self.embedding_query = data.get("embedding_query", "")
            self.lang = data.get("original_language", "en")

            if data["online"] == True:
                await self.send_response([], [], "Debes mencionar explícitamente que se está realizando una búsqueda online respecto a la pregunta del usuario y que este debe esperar.", "await")
                await self.send("crawler", self.embedding_query)
                return

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

            print("[BUSCANDO INFORMACIÓN EN LAS BASES DE CONOCIMIENTOS]")

            # Construir payload común
            payload_ontology = {"cocktails": cocktail_names, "fields": field_sets}
            payload_embedding = {"query": self.embedding_query}

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
            if 'error' in message["content"]:
                print("[EMITIENDO RESPUESTA]\n")
                await self.send_response([], [], "Información al respecto no encontrada", "error")
            else:
                content = message["content"]["suficiencia"]
                drinks = message["content"]["drinks"]
                extra = message["content"]["extra"]
                suficiente = content["suficiente"]
                expandida_suficiente = content["expandida_suficiente"]
                razonamiento = content["razonamiento"]
                online = content["online"]
                if suficiente == True or expandida_suficiente==True:
                    
                    # Enviando respuesta
                    print("[EMITIENDO RESPUESTA]\n")
                    await self.send_response(drinks, extra, razonamiento, "final")

                    # Limpiando memoria
                    self.lang = "en"
                    self.query = "Empty query"
                
                elif online:
                    print("[EMITIENDO RESPUESTA]\n")
                    await self.send_response([], [], "Información al respecto no encontrada. Debes mencionar explícitamente que se está realizando una búsqueda online respecto a la pregunta del usuario y que este debe esperar.", "await")
                    await self.send("crawler", self.embedding_query)

                else:
                    print("[EMITIENDO RESPUESTA]\n")
                    await self.send_response(drinks, extra, "Intenta responder con lo que tengas", "final")

        elif sender=="crawler":
            
            await self.send_response(message["content"]["results"], [], "Resultado de realizar la busqueda online.", "final")
                    
        

    async def send_response(self, respuesta, complementos, razonamiento, intencion):
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
    If you see in the reasoning something like "Información al respecto no encontrada. Realizando búsqueda online." You should mention to the user that his request is being searched online and that he should wait.
    On that case, the user should wait for your answer and will not be able to insert an input, so don't try to tell him to do anything else but wait.
    """

        try:
            # Enviar el prompt al modelo (asumiendo método generate)
            output = self.model.generate_content(prompt)

            # Extraer texto limpio
            final_answer = output.text.strip() if hasattr(output, 'text') else str(output).strip()

            # Enviar la respuesta al UserAgent (simulado aquí con un print, reemplaza con tu entorno de mensajes)
            await self.send("user", {
                "type": "respuesta_final",
                "content": final_answer,
                "intencion": intencion
            })

        except Exception as e:
            await self.send("user", {
                "type": "respuesta_final",
                "content": f"Sorry, I was unable to generate a final answer due to an internal error: {str(e)}"
            })

