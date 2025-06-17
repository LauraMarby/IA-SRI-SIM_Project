import pickle
from agents.base_agent import BaseAgent

class EmbeddingAgent(BaseAgent):
    """
    Agente responsable de recuperar información basada en vectores.

    Dado un texto de consulta, este agente transforma la pregunta a su representación
    vectorial y realiza una búsqueda de similitud en un repositorio de embeddings 
    previamente indexado. Retorna los fragmentos más relevantes.

    Responsabilidades:
    - Generar embeddings de la consulta.
    - Consultar una base vectorial local.
    - Devolver los documentos más similares.

    """
    def __init__(self, name, system, embedding_fn):
        """
        Inicializa el agente de recuperación por embeddings.

        Este agente se encarga de recibir una consulta vectorial, buscar entre los
        embeddings precargados los documentos más relevantes, y enviar los resultados
        al agente validador para su evaluación.

        Args:
            name (str): Nombre del agente.
            system (System): Referencia al sistema multiagente.
            embedding_fn (Callable): Función que toma una consulta y un embedding indexado,
                                     y devuelve los documentos más relevantes.
        """
        super().__init__(name, system)
        self.embedding_fn = embedding_fn
        # Declarar vectores del embedding y asignarlos
        with open("src/embedding/embeddings.pkl", 'rb') as f:
            self.data = pickle.load(f)

    async def handle(self, message):
        """
        Maneja una consulta enviada al agente embedding.

        Extrae la consulta del mensaje, realiza la búsqueda vectorial y envía los 
        resultados al agente validador.

        Args:
            message (dict): Mensaje con el campo "content.query" como texto para consultar.
        """
        query = message["content"]["query"]
        # Preprocesar la query
        print("[CONSULTANDO AL REPOSITORIO VECTORIAL]")
        results = self.embedding_fn(query, self.data)
        await self.send("validator", {"source": "embedding", "results": results, "type": "result"})