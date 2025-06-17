from agents.base_agent import BaseAgent
import json
import re
import ast
import asyncio
from utils.metaheuristic import TabuSearchSelector

class ValidationAgent(BaseAgent):
    """
    Agente responsable de validar y filtrar la información recopilada desde diferentes fuentes
    (ontología, embedding, web) para construir una respuesta precisa y consistente.

    Su trabajo principal es:
    - Esperar resultados desde múltiples fuentes.
    - Aplicar restricciones semánticas (fuertes y débiles) derivadas de la consulta del usuario.
    - Evaluar subconjuntos de candidatos con una metaheurística (Tabu Search).
    - Verificar la suficiencia de los elementos seleccionados antes de enviarlos al Coordinador.
    """

    def __init__(self, name, system, model, alpha=100, beta=1, gamma=2, num_ants=10, max_iters=20):
        """
    Inicializa el agente validador.

    Args:
        name (str): Nombre identificador del agente.
        system (System): Referencia al sistema multiagente (mensajería y orquestación).
        model: Modelo de lenguaje usado para derivar restricciones semánticas a partir de la consulta.
        alpha (int): Parámetro para exploración/explotación en metaheurísticas (no usado en Tabu).
        beta (int): Parámetro de penalización.
        gamma (int): Peso de las restricciones débiles.
        num_ants (int): Cantidad de agentes en metaheurísticas basadas en colonia (no usado aquí).
        max_iters (int): Número máximo de iteraciones para búsqueda de soluciones.
    """
        super().__init__(name, system)
        self.model = model
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.num_ants = num_ants
        self.max_iters = max_iters
        self.expected_sources = set()
        self.received_data = {}
        self.query = None

    async def handle(self, message):
        """
        Procesa mensajes entrantes desde otros agentes.

        - Si el mensaje es del tipo "expectation", se inicializan las fuentes esperadas y la consulta.
        - Si es del tipo "result", se acumulan los resultados por fuente.
        - Cuando todas las fuentes esperadas han respondido, se:
            - Unifican y normalizan los candidatos.
            - Elimina duplicados.
            - Extraen restricciones fuertes y débiles desde el modelo.
            - Verifica subconjuntos válidos usando una matriz de cumplimiento.
            - Ejecuta Tabu Search para encontrar el subconjunto óptimo.
            - Verifica la suficiencia semántica de la respuesta final.
            - Envía el resultado final al Coordinador.

        En caso de error, se notifica al Coordinador con un mensaje de error.
        """
        
        try:
            content = message.get("content", {})
            msg_type = content.get("type")

            if msg_type == "expectation":
                self.expected_sources = set(content.get("sources", []))
                self.received_data.clear()
                self.query = content.get("query")
                return

            if msg_type != "result":
                return  # Ignorar otros tipos por ahora

            source = content.get("source")
            results = content.get("results", [])

            # Guardar resultados solo si son de una fuente esperada
            if source not in self.expected_sources:
                return

            self.received_data[source] = results

            # Si aún no recibimos todos, esperar
            if not self.expected_sources.issubset(self.received_data.keys()):
                return

            print("[CONFORMANDO CONJUNTO DE DATOS PARA LA RESPUESTA]")

            # Recolectar y normalizar candidatos
            candidates = []
            for src in self.expected_sources:
                for result in self.received_data.get(src, []):
                    candidates.append(self.stringify_candidate(result))

            if not candidates:
                await self.send("coordinator", {"error": "No se encontraron candidatos para evaluar."})
                self._clear_state()
                return

            candidates = eliminar_repetidos(candidates)

            # Extraer restricciones
            restrictions = self.extract_constraints(self.query)
            if not restrictions.get("fuertes"):
                await self.send("coordinator", {"error": "No se pudieron extraer restricciones fuertes válidas."})
                self._clear_state()
                return

            # Crear matriz de verificación
            all_restrictions = restrictions["fuertes"] + restrictions["débiles"]
            matriz = self.verifica_matriz(candidates, all_restrictions)
            filtered_candidates, _ = divide(candidates, len(matriz))
            
            while True:
                try:
                    selector = TabuSearchSelector(alpha=10, beta=1, gamma=2, max_iters=200)
                    selected, puntaje = selector.select(filtered_candidates, restrictions, matriz)
                    break  # Éxito, salimos del bucle
                except Exception as e:
                    print(f"[ACO] Error durante la ejecución: {e}. Reintentando...")
                    await asyncio.sleep(0.1)  # Pequeña pausa opcional para evitar bucles frenéticos
            
            # Metaheurística descartada.
            # while True:
            #     try:
            #         selected, score = self.ant_colony_optimization(candidates, restrictions, matriz)
            #         break  # Éxito, salimos del bucle
            #     except Exception as e:
            #         print(f"[ACO] Error durante la ejecución: {e}. Reintentando...")
            #         await asyncio.sleep(0.1)  # Pequeña pausa opcional para evitar bucles frenéticos

            # Verificar suficiencia
            restricciones_conjuntas = restrictions.get("conjuntas", [])
            print("[VALIDANDO CONTENIDO DE LA RESPUESTA]")
            suficiencia = self.verifica_suficiencia(self.query, selected, candidates, restricciones_conjuntas)

            # Enviar resultado final al coordinator
            await self.send("coordinator", {"suficiencia": suficiencia, "drinks": selected, "extra": candidates})

            self._clear_state()

        except Exception as e:
            await self.send("coordinator", {"error": f"Error inesperado en ValidationAgent: {str(e)}"})

    def _clear_state(self):
        """
        Limpia el estado interno del agente entre consultas.

        Se eliminan:
        - Fuentes esperadas.
        - Datos recibidos.
        - Consulta en curso.
        """
        self.expected_sources.clear()
        self.received_data.clear()
        self.query = None

    def extract_constraints(self, query):

        """
        Genera restricciones semánticas a partir de la consulta original del usuario.

        Utiliza el modelo de lenguaje para clasificar restricciones en:
        - Fuertes: obligatorias para cumplir con los requisitos explícitos.
        - Débiles: deseables pero no obligatorias.
        - Conjuntas: aplican sobre la cantidad o combinación de resultados.

        El formato del JSON devuelto es:
        {
            "fuertes": [ ... ],
            "débiles": [ ... ],
            "conjuntas": [ ... ]
        }

        Args:
            query (str): Consulta original del usuario.

        Returns:
            dict: Diccionario con listas de restricciones clasificadas.

        Lanza:
            ValueError: Si el modelo no produce una salida válida.
        """

        prompt = f"""
Eres un asistente para procesar consultas de usuarios sobre cocteles y tragos. Dada esta consulta de usuario: \"{query}\"

Extrae las restricciones de contenido que debe cumplir una buena respuesta. Estas restricciones deben clasificarse en fuertes y débiles.\n"
Las restricciones fuertes son aquellas que garantizan todo lo que se menciona explícitamente en la pregunta respecto a un trago o tragos, y debe ser un conjunto pequeño de restricciones separadas, representando cada problemática a resolver de la pregunta. Cada restricción debe ser un texto lo más básico y pequeño posible. No incluya restricciones de tragos conjuntos, separe en problemáticas por cada trago."
Las restricciones débiles son aquellas que no se tienen que cumplir necesariamente, pero aporta valor a la calidad de la respuesta. Debe ser un conjunto pequeño también, de restricciones separadas. No incluya restricciones de tragos conjuntos, separe en problemáticas por cada trago."
Cada restricción debe estar orientada exclusivamente a un problema que debe cumplirse respecto a un único trago. Además, cada candidato de respuesta corresponde también a un único trago, así que ningún documento contendrá independientemente varias recetas sobre varios tragos, por lo cual este tipo de restricciones debe quedar situada en otro campo.
Devuelva un JSON con el siguiente formato:\n
fuertes: [Todas las restricciones fuertes respecto a cada trago. Esto debe ser una lista de string]\n
débiles: [Lista o conjunto de restricciones débiles. Esto debe ser una lista de string]\n
conjuntas: [Conjunto de restricciones que se debe cumplir en general, y depende de la cantidad de tragos y especificación de los mismos que requiere la pregunta.]
NOTA: Ninguna de las restricciones extraidas debe ser algo ambiguo, tienen que ser afirmaciones fácilmente verificables y explícitas. Además, ignora restricciones que no traten explícitamente sobre la bebida en cuestión.
"""
        response = self.model.generate_content(prompt)
        
        if not response or not getattr(response, "text", None):
            raise ValueError("La salida del modelo está vacía o malformada")

        try:
            text = response.text.strip()
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
            else:
                text = text.strip('`\n')

            text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
            parsed = json.loads(text)
            parsed.setdefault("restricciones_fuertes_conjuntas", [])
            return parsed

        except Exception as e:
            print(f"[ValidationAgent] Error parsing restricciones:\n{response.text}\n{e}")
            return {"restricciones_fuertes": [], "restricciones_debiles": []}

    # def ant_colony_optimization(self, candidates, restrictions, matriz):
    #     self.all_candidates = candidates  # ✅ Asignamos para uso global en esta instancia

    #     pheromones = [1.0] * len(candidates)
    #     best_solution = None
    #     best_score = float("-inf")
    #     seen_keys = set()

    #     try:
    #         for _ in range(self.max_iters):
    #             for _ in range(self.num_ants):
    #                 solution = self.construct_solution(candidates, pheromones)

    #                 # ⚠️ Normalizamos la solución: orden y sin repeticiones
    #                 solution = sorted(set(solution), key=lambda x: str(x))
    #                 key = tuple(solution)

    #                 if key in seen_keys:
    #                     continue

    #                 seen_keys.add(key)
    #                 score = self.evaluate_fitness(solution, restrictions, matriz)

    #                 if score > best_score:
    #                     best_score = score
    #                     best_solution = solution

    #             pheromones = self.update_pheromones(
    #                 [([s for s in best_solution], best_score)] if best_solution else [],
    #                 pheromones
    #             )

    #         if best_solution:
    #             return best_solution, best_score
    #         else:
    #             raise ValueError("No se encontró solución óptima")

    #     except Exception as e:
    #         print(f"[WARNING] Error en ACO: {e}")

    #         # Buscar un candidato que cumpla la mayoría de restricciones
    #         num_fuertes = len(restrictions["fuertes"])
    #         mejor_idx = None
    #         mejor_score = float("-inf")

    #         for idx, vector in enumerate(matriz):
    #             fuertes_cumplidas = sum(vector[:num_fuertes])
    #             debiles_cumplidas = sum(vector[num_fuertes:])
    #             score = self.alpha * fuertes_cumplidas + self.beta * debiles_cumplidas - self.gamma * 1

    #             if score > mejor_score:
    #                 mejor_score = score
    #                 mejor_idx = idx

    #         if mejor_idx is not None:
    #             return [candidates[mejor_idx]], mejor_score
    #         else:
    #             # Si ni siquiera eso se puede, devuelve el primero
    #             return [candidates[0]], -10000

    # def construct_solution(self, candidates, pheromones):
    #     num_to_select = min(5, len(candidates))
    #     total_pheromones = sum(pheromones)
    #     selected_indices = set()

    #     while len(selected_indices) < num_to_select:
    #         # Recalcular el total de feromonas solo de los disponibles
    #         available_indices = [i for i in range(len(candidates)) if i not in selected_indices]
    #         if not available_indices:
    #             break  # ya no hay más para seleccionar

    #         total_pheromones = sum(pheromones[i] for i in available_indices)
    #         r = random.uniform(0, total_pheromones)
    #         cumulative = 0.0

    #         for i in available_indices:
    #             cumulative += pheromones[i]
    #             if cumulative >= r:
    #                 selected_indices.add(i)
    #                 break

    #     return [candidates[i] for i in selected_indices]

    # def evaluate_fitness(self, solution, restrictions, matriz):
    #     fuertes = restrictions["fuertes"]
    #     debiles = restrictions["débiles"]

    #     # Índices de restricciones
    #     num_fuertes = len(fuertes)
    #     num_debiles = len(debiles)

    #     # Inicializamos vectores de cumplimiento conjunto
    #     cumples_f = [False] * num_fuertes
    #     cumples_d = [False] * num_debiles

    #     for cand in solution:
    #         try:
    #             idx = next((i for i, c in enumerate(self.all_candidates) if str(c) == str(cand)), None)
    #             if idx is None:
    #                 continue
    #             vector = matriz[idx]
    #             for i in range(num_fuertes):
    #                 cumples_f[i] = cumples_f[i] or vector[i]
    #             for j in range(num_debiles):
    #                 cumples_d[j] = cumples_d[j] or vector[num_fuertes + j]
    #         except ValueError:
    #             continue  # Si por alguna razón el candidato no está

    #     # Ponderación: penaliza si no cumple todas las fuertes
    #     if not all(cumples_f):
    #         return -10000

    #     debiles_cumplidas = sum(cumples_d)
    #     return self.alpha * num_fuertes + self.beta * debiles_cumplidas - self.gamma * len(solution)

    # def update_pheromones(self, solutions, pheromones):
    #     decay = 0.3
    #     pheromones = [p * (1 - decay) for p in pheromones]

    #     for solution, score in solutions:
    #         for c in solution:
    #             try:
    #                 idx = self.all_candidates.index(c)
    #                 pheromones[idx] += score / 100.0
    #             except ValueError:
    #                 pass
    #     return pheromones

    def verifica_matriz(self, respuestas, restricciones):
        """
        Evalúa una lista de respuestas candidatas contra un conjunto de restricciones
        (fuertes y/o débiles) y devuelve una matriz booleana indicando el cumplimiento.

        Cada fila representa una respuesta candidata y cada columna una restricción.
        El valor en [i][j] es True si la respuesta i cumple la restricción j, False en caso contrario.

        La evaluación se realiza mediante una consulta a un modelo de lenguaje, que responde
        en formato JSON indicando "sí"/"no" para cada par respuesta-restricción.

        Args:
            respuestas (list of str): Lista de respuestas candidatas normalizadas.
            restricciones (list of str): Lista de restricciones a verificar.

        Returns:
            list of list of bool: Matriz de cumplimiento (True/False) por respuesta y restricción.
        """

        prompt = f"""
        Tenemos una lista de respuestas candidatas y una lista de restricciones.
        Para cada respuesta, indica si cumple cada restricción (sí o no). 
        Responde en formato JSON como una lista de objetos, uno por respuesta. 
        Cada objeto debe tener esta estructura: 
        {{"respuesta": "texto", "cumple": ["sí", "no", "sí", ...]}}
        Respuestas:
        {json.dumps(respuestas[:200], ensure_ascii=False)}
        Restricciones:
        {json.dumps(restricciones, ensure_ascii=False)}
        """

        try:
            output = self.model.generate_content(prompt)

            if not output or not getattr(output, "text", None):
                raise ValueError("La salida del modelo está vacía o malformada")

            text = output.text.strip().replace("“", "\"").replace("”", "\"")

            # Intentar extraer bloque JSON con regex
            match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)

            # parsed = json.loads(text)
            parsed = extraer_respuestas_crudas(text)

            cumplimientos = []

            for obj in parsed:
                cumple = obj.get("cumple", [])

                # Convertir cada "sí"/"no" en bool
                vector_bool = ["sí" in estado.lower() for estado in cumple]
                cumplimientos.append(vector_bool)

            return cumplimientos

        except Exception as e:
            print(f"[ValidationAgent] Error en verifica_matriz:\n{e}")
            print(f"[ValidationAgent] Output del modelo:\n{getattr(output, 'text', '')}")
            return {(r, c): False for c in respuestas for r in restricciones}

    def verifica_suficiencia(self, pregunta, respuestas, candidates, restricciones_grupales):
        """
        Evalúa si el conjunto seleccionado de respuestas contiene información suficiente
        para responder la pregunta del usuario de forma completa y válida, según un conjunto
        de restricciones conjuntas y secundarias.

        Utiliza un modelo de lenguaje para analizar si:
        - Las respuestas seleccionadas bastan para cumplir los requisitos ("suficiente").
        - Algunas respuestas adicionales podrían mejorar o completar la respuesta ("expandida_suficiente").
        - Se necesita hacer una búsqueda en línea debido a limitaciones del conocimiento disponible.

        Args:
            pregunta (str): Consulta original del usuario.
            respuestas (list of str): Fragmentos seleccionados como núcleo de la respuesta.
            candidates (list of str): Resto de fragmentos disponibles como información secundaria.
            restricciones_grupales (list of str): Reglas que deben cumplirse para toda la respuesta combinada.

        Returns:
            dict: Diccionario con claves:
                - "suficiente": bool
                - "expandida_suficiente": bool
                - "razonamiento": str
                - "online": bool
        """

        prompt = f"""
        Tengo una pregunta que realizó un usuario, y tengo información que puedo usar para conformar una respuesta.

Pregunta del usuario:
"{pregunta}"

Información que considero importante:
{[r for r in respuestas]}

Información que considero útil y secundaria:
{[r for r in candidates]}

Además, estas son las restricciones que debe cumplir una buena respuesta, además de las que puedas inferir por la pregunta del usuario:
{[r for r in restricciones_grupales]}

Tu respuesta debe ser un OBJETO JSON con la siguiente estructura exacta, usando solo tipos válidos de JSON (booleanos, listas, cadenas, etc.), **sin poner todo como texto ni concatenar campos**:

```json
{{
  "suficiente": Indica si con la información importante es suficiente o no dar una respuesta correcta que cumpla las restricciones.
  "expandida_suficiente": Indica si agregando algunos de los fragmentos extra, es suficiente o no dar una respuesta correcta que cumpla las restricciones.
  "razonamiento": "..."
  "requiere_búsqueda_online": True o False. Esto depende del contexto de la pregunta. Por ejemplo si me piden un trago que no encuentro, esto debe ser True, pero si me piden algo como (Recomiendame algo) sin dar detalles de sus gustos, esto debe ser falso porque cualquier trago podría gustar.
  **NOTA IMPORTANTE: Si la pregunta del usuario implica explícitamente una búsqueda en internet, requiere_búsqueda_online debe ser True.**
}}
"""

        response = self.model.generate_content(prompt)

        if not response or not getattr(response, "text", None):
            raise ValueError("La salida del modelo está vacía o malformada")

        raw_text = response.text
        cleaned = manual_json_extract(raw_text)

        return cleaned

    def stringify_candidate(self, candidate):
        """
        Convierte un candidato (puede ser string o dict) a una representación
        de texto estándar para su análisis posterior por un modelo de lenguaje.

        Si el candidato es un diccionario, se transforma a una cadena en formato:
        "clave1: valor1 | clave2: valor2 | ...", con listas también representadas como strings.

        Args:
            candidate (str or dict): Fragmento de información sobre un trago.

        Returns:
            str: Representación textual del candidato.
        """
        
        if isinstance(candidate, str):
            return candidate

        if isinstance(candidate, dict):
            parts = []
            for key, value in candidate.items():
                # Convertir listas a string legible
                if isinstance(value, list):
                    value_str = "[" + ", ".join(map(str, value)) + "]"
                else:
                    value_str = str(value)

                parts.append(f"{key}: {value_str}")

            return " | ".join(parts)

        return str(candidate)

def extraer_respuestas_crudas(texto):
    """
    Extrae manualmente los pares respuesta + cumple de un texto tipo JSON malformado.
    Retorna una lista de diccionarios válidos para json.loads.
    """
    # Extraer manualmente cada bloque de respuesta con su lista "cumple"
    pattern = re.compile(
        r'"respuesta"\s*:\s*"(?P<respuesta>.*?)"\s*,\s*"cumple"\s*:\s*(?P<cumple>\[[^\]]+\])',
        re.DOTALL
    )

    resultados = []
    for match in pattern.finditer(texto):
        raw_respuesta = match.group("respuesta")
        raw_cumple = match.group("cumple")

        # Limpiar respuesta y cumple
        respuesta = raw_respuesta.strip().replace('\n', ' ').replace('\\"', '"').replace('"', "'")
        try:
            cumple = json.loads(raw_cumple)
        except json.JSONDecodeError:
            continue  # Saltar si no puede interpretarse la lista cumple

        resultados.append({
            "respuesta": respuesta,
            "cumple": cumple
        })

    return resultados

def manual_json_extract(text):
    """
    Extrae manualmente los campos de interés desde un bloque textual que aparenta ser un JSON malformado.
    Devuelve un diccionario válido con los campos esperados.
    """
    campos = {
        "suficiente": None,
        "expandida_suficiente": None,
        "respuesta_expandida": [],
        "campos_suficientes": [],
        "razonamiento": ""
    }
        
    def extract_bool(name):
        pattern = rf'"{name}"\s*:\s*(true|false)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).lower() == "true"
        return None

    def extract_list(name):
        pattern = rf'"{name}"\s*:\s*\[(.*?)\]'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = f"[{match.group(1)}]"
            try:
                return ast.literal_eval(content)
            except Exception:
                return []
        return []

    def extract_string(name):
        pattern = rf'"{name}"\s*:\s*"(.*?)"'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    campos["suficiente"] = extract_bool("suficiente")
    campos["expandida_suficiente"] = extract_bool("expandida_suficiente")
    campos["campos_suficientes"] = extract_list("campos_suficientes")
    campos["razonamiento"] = extract_string("razonamiento")
    campos["online"] = extract_bool("requiere_búsqueda_online")

    return campos

def extraer_por_prefijo(X, Y):
    """
    Devuelve un diccionario donde cada clave de Y contiene todos los fragmentos de X
    que comienzan con ese prefijo exacto.
    """
    resultado = {y: [] for y in Y}
    for y in Y:
        for x in X:
            if x.startswith(y):
                resultado[y].append(x)
    return resultado

def eliminar_repetidos(lista_textos):
    vistos = set()
    resultado = []
    for texto in lista_textos:
        if texto not in vistos:
            resultado.append(texto)
            vistos.add(texto)
    return resultado

def divide(lista, n):
    """
    Divide la lista en dos partes:
    - La primera con los primeros n elementos
    - La segunda con el resto de elementos

    Parámetros:
        lista (list): lista original
        n (int): tamaño del primer segmento

    Retorna:
        tuple: (lista picada, resto de la lista)
    """
    primera_parte = lista[:n]
    resto = lista[n:]
    return primera_parte, resto
