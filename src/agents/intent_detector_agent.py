from agents.base_agent import BaseAgent

class IntentDetectorAgent(BaseAgent):
    """
    Agente responsable de detectar la intención del usuario a partir de su consulta textual.

    Este agente se comunica con un modelo de lenguaje para analizar la consulta, identificar
    menciones de cócteles, campos requeridos, sabores, posibles búsquedas por embedding o en línea,
    y devuelve una estructura JSON con la interpretación detallada de la intención.
    """
    def __init__(self, name, system, model):
        """
        Inicializa el agente detector de intenciones.

        Args:
            name (str): Nombre del agente.
            system (System): Referencia al sistema multiagente.
            model: Modelo de lenguaje definido para realizar consultas.
        """
        super().__init__(name, system)
        self.model = model

    async def run(self):
        """
        Bucle principal del agente.

        Escucha mensajes entrantes, ejecuta el análisis de intención sobre la consulta recibida,
        y reenvía el resultado (en formato JSON) al agente que originó la consulta.
        """
        while True:
            msg = await self.receive()
            query = msg["content"]
            sender = msg["from"]

            intent_json = await self.detect_intent(query)

            await self.send(sender, intent_json)

    async def detect_intent(self, query):
        """
        Llama al modelo de lenguaje para interpretar la intención de una consulta de usuario.

        Genera un prompt detallado con instrucciones precisas para que el modelo identifique:
        - Idioma original
        - Traducción al inglés
        - Si se menciona un cóctel o no
        - Los campos solicitados sobre cada cóctel
        - Fórmulas lógicas sobre sabores (si se pide recomendación sin mencionar cóctel)
        - Preguntas independientes para el embedding
        - Si se requiere búsqueda en línea

        Args:
            query (str): Consulta del usuario en lenguaje natural.

        Returns:
            str: Respuesta generada por el modelo, con un JSON estructurado como salida.
        """

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
        - "name": nombre del cóctel. Este campo no puede ser vacío, debe mencionar el coctel que se quiere buscar.
        - "fields_requested": una lista de 9 valores booleanos, uno por cada campo del cóctel (en este orden: {', '.join(CAMPOS_TRAGO)}). Pon `true` si el usuario quiere saber sobre ese campo, `false` en caso contrario.
        Este campo no debe tener nombres no especificados, aunque el requisito sea obtener algo de esos tragos. Si no se conoce el nombre del trago, no se incluye aquí, se incluye en las preguntas del embedding.
        - "flavors": Por cada trago desconocido pedido en una recomendación, se debe dar una descripción de la forma categoría_sabor. Las categorías son **nada**, **poco**, **medio** o **muy** (en base a que tanto predomina ese sabor en el trago) y los sabores son **dulce**, **salado**, **ácido**, **amargo**, **picante**. Si hay varias categorías, debes separarlas con un AND (ejemplo: muy_dulce AND poco_salado). Si hay varios tragos, debes separarlos con un or (ejemplo: muy_dulce AND poco_salado OR medio_dulce AND medio_ácido). **Es muy importante que las formulas no se salgan de lo especificado (las 5 palabras de sabor y las 4 palabras de categoría)**
        - "embedding_query": a partir de la consulta inicial, realice una o varias preguntas que se deban consultar con el embedding. Estas preguntas deben tratar un problema independiente de los problemas que tiene la consulta respecto a cada trago. Esto debe incluir datos específicos de la consulta original, como contexto global o cantidades a resolver. Estas consultas deben estar en inglés. Cada consulta debe ser un elemento de este campo. Si solo se puede realizar una única consulta, este campo debe ser un conjunto de un elemento. Estas consultas deben ser lo más pequeñas posibles, no pasarse de 20 tokens.
        - "online": Si el usuario menciona explicitamente hacer una búsqueda en internet, este campo debe ser True y se usarán los campos de embedding_query para esta búsqueda. De lo contrario este campo será False.
        NOTA: Si el usuario no menciona nada respecto a un trago, más que su nombre, asume que quiere saber sus ingredientes y su preparación, pero no dejes todos los datos del trago en false.
        """
        print("\n[DETECTANDO INTENCIONES DE LA CONSULTA]")
        response = self.model.generate_content(prompt)
        return response.text