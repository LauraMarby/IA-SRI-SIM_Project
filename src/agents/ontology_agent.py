import os
from owlready2 import get_ontology
from agents.base_agent import BaseAgent

class OntologyAgent(BaseAgent):
    """
    Agente responsable de recuperar información estructurada sobre cócteles desde la ontología OWL.

    Este agente recibe una lista de cócteles y campos requeridos, consulta la ontología cargada en memoria
    usando una función de consulta externa, y envía los resultados filtrados al agente validador.
    """
    def __init__(self, name, system, ontology_fn):
        """
        Inicializa el agente de ontología y carga el archivo OWL.

        Args:
            name (str): Nombre identificador del agente.
            system (System): Referencia al sistema multiagente (contexto de ejecución y comunicación).
            ontology_fn (Callable): Función que permite realizar consultas sobre la ontología cargada.
        """
        super().__init__(name, system)
        self.ontology_fn = ontology_fn
        ONTOLOGY_PATH = os.path.abspath("src/ontology/ontology.owl")
        self.onto = get_ontology(f"file://{ONTOLOGY_PATH}").load()

    async def handle(self, message):
        """
        Maneja un mensaje entrante con una consulta sobre cócteles y campos.

        Procesa el mensaje recibido, consulta la ontología usando la función `ontology_fn`, y
        filtra los resultados con errores antes de reenviarlos al agente validador.

        Args:
            message (dict): Mensaje con las siguientes claves:
                - content["cocktails"]: Lista de nombres de cócteles a consultar.
                - content["fields"]: Lista de listas booleanas, cada una indicando qué campos se deben obtener.
        """
        cocktail = message["content"]["cocktails"]
        fields = message["content"]["fields"]
        print("[CONSULTANDO A LA ONTOLOGÍA]")
        results = self.ontology_fn(cocktail, fields, self.onto)
        filtered_results = []
        for result in results:
            if "Error" not in result:
                filtered_results.append(result)
        await self.send("validator", {"source": "ontology", "results": filtered_results, "type": "result"})