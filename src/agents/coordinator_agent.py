import json
import re
from agents.base_agent import BaseAgent

TEST = False

class CoordinatorAgent(BaseAgent):
    """
    Agente coordinador del sistema.

    Se encarga de recibir las consultas del usuario, detectar la intención
    o tipo de búsqueda, y distribuir tareas a los agentes adecuados (como 
    OntologyAgent, EmbeddingAgent, Flavor_Agent, etc.). Una vez recibidas 
    las respuestas, las pasa al ValidationAgent para su evaluación.

    Responsabilidades:
    - Detectar la intención de la consulta del usuario.
    - Gestionar el flujo de mensajes entre agentes.
    - Consolidar la información y controlar el ciclo de validación.
    - Reenviar la respuesta final al usuario.

    """
    
    def __init__(self, name, system, model):
        """
        Inicializa el agente coordinador.

        Args:
            name (str): Nombre del agente.
            system (System): Referencia al sistema multiagente.
            model (Any): Modelo de lenguaje utilizado para generar respuestas.
        """
        super().__init__(name, system)
        self.model = model
        self.lang = "en"
        self.query = "Empty query"
        self.embedding_query = []

    async def handle(self, message):
        """
        Maneja los mensajes entrantes según su origen (user, validator, crawler).

        Dependiendo del emisor del mensaje, coordina el flujo de consulta entre 
        agentes de ontología, embeddings, validador, crawler, y sabores.

        Args:
            message (dict): Mensaje recibido, debe incluir 'from' y 'content'.
        """
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
            flavors = data.get("flavors", [])
            if flavors is not None:
                expected_sources.append("flavor")

            # Avisar al validador de qué fuentes esperar
            if expected_sources:
                await self.send("validator", {
                    "type": "expectation",
                    "sources": expected_sources,
                    "query": self.query  # útil para que el validador sepa qué validar
                })

            if flavors is not []:
                print("[CONSULTANDO AGENTE DE SABORES]")
                await self.send("flavor", {"flavors": flavors, "ammount": 5})
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
        """
        Construye y envía la respuesta final al usuario.

        Utiliza el modelo de lenguaje para generar una respuesta final en el idioma
        del usuario, a partir de la información recuperada y el razonamiento aplicado.

        Args:
            respuesta (Any): Información seleccionada como más relevante.
            complementos (Any): Datos adicionales útiles para enriquecer la respuesta.
            razonamiento (str): Justificación para haber elegido esa respuesta.
            intencion (str): Tipo de respuesta ("final", "await", "error", etc.).
        """
        
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

