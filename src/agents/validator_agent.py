import random
from agents.base_agent import BaseAgent
import json
import re

class ValidationAgent(BaseAgent):
    def __init__(self, name, system, model, alpha=100, beta=1, gamma=2, num_ants=10, max_iters=20):
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
        content = message["content"]
        msg_type = content.get("type")

        if msg_type == "expectation":
            self.expected_sources = set(content.get("sources", []))
            self.received_data = {}
            self.query = content.get("query")

        elif msg_type == "result":
            source = content.get("source")
            results = content.get("results", [])

            # Guardar resultados solo si son de una fuente esperada
            if source in self.expected_sources:
                self.received_data[source] = results

            # Esperar hasta recibir TODAS las fuentes esperadas
            if self.expected_sources.issubset(self.received_data.keys()):
                # Combinar candidatos de todas las fuentes recibidas
                candidates = []
                for src in self.expected_sources:
                    candidates.extend(self.received_data.get(src, []))
                
                for i in range(len(candidates)):
                    if not isinstance(candidates[i], str):
                        candidates[i] = self.stringify_candidate(candidates[i])

                restrictions = await self.extract_constraints(self.query, candidates)
                selected = await self.ant_colony_optimization(candidates, restrictions)

                # ⚠️ Verificación de suficiencia con el modelo de lenguaje
                restricciones_conjuntas = restrictions.get("restricciones_fuertes_conjuntas", [])
                suficiencia = await self.verifica_suficiencia(self.query, selected, candidates, restricciones_conjuntas)

                # Enviar resultado completo al coordinator
                await self.send("coordinator", {
                    "suficiencia": suficiencia,
                })

                # Limpiar estado interno
                self.expected_sources = set()
                self.received_data = {}
                self.query = None

    async def extract_constraints(self, query, candidates):
        prompt = f"""
Eres un asistente para procesar consultas de usuarios sobre cocteles y tragos. Dada esta consulta de usuario: \"{query}\"
y las siguientes respuestas candidatas:
{[c[:200] for c in candidates]}

Extrae las restricciones que debe cumplir una respuesta válida.
Clasifica cada una en tres categorías:
- restricciones_fuertes: obligatorias que debe cumplir cada respuesta individualmente. Este campo no debe quedar vacío. Si se mencionan varias recetas, este campo no debe contener algo específico de ninguna, solo una condición que todas deban cumplir.
- restricciones_debiles: deseables que debe cumplir cada respuesta individual.
- restricciones_fuertes_conjuntas: que deben cumplirse por el conjunto completo de respuestas (por ejemplo, “recomendar varios tragos”, “que todos los tragos sean del mismo país”, etc.)

Devuelve en formato JSON:
{{
  "restricciones_fuertes": [...],
  "restricciones_debiles": [...],
  "restricciones_fuertes_conjuntas": [...]
}}
"""
        response = await self.model.generate_content_async(prompt)
        
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

    async def ant_colony_optimization(self, candidates, restrictions):
        all_restrictions = restrictions["restricciones_fuertes"] + restrictions["restricciones_debiles"]
        verificados = await self.verifica_matriz(candidates, all_restrictions)

        pheromones = [1.0] * len(candidates)
        best_solution = None
        best_score = float("-inf")
        seen_keys = set()

        for _ in range(self.max_iters):
            for _ in range(self.num_ants):
                solution = self.construct_solution(candidates, pheromones, restrictions)

                # ⚠️ Normalizamos la solución: orden y sin repeticiones
                solution = sorted(set(solution), key=lambda x: str(x))
                key = tuple(solution)  # hashable y ordenado

                if key in seen_keys:
                    continue  # ya fue evaluada

                seen_keys.add(key)
                score = self.evaluate_fitness(solution, restrictions, verificados)

                if score > best_score:
                    best_score = score
                    best_solution = solution

            # Actualizar feromonas solo con la mejor solución de esta iteración
            pheromones = self.update_pheromones(
                [([s for s in best_solution], best_score)] if best_solution else [],
                pheromones
            )

        return best_solution, best_score

    def construct_solution(self, candidates, pheromones, restrictions):
        solution = []
        for i, c in enumerate(candidates):
            p = pheromones[i] * random.uniform(0.5, 1.5)
            if random.random() < p / (p + 1):
                solution.append(c)
        return solution

    def evaluate_fitness(self, solution, restrictions, verificados):
        fuertes = restrictions["restricciones_fuertes"]
        debiles = restrictions["restricciones_debiles"]

        # Validar fuertes individuales
        for r in fuertes:
            if not any(verificados.get((c, r), False) for c in solution):
                return -10000

        # Validar débiles
        debiles_cumplidas = sum(
            any(verificados.get((c, r), False) for c in solution) for r in debiles
        )

        return self.alpha * len(fuertes) + self.beta * debiles_cumplidas - self.gamma * len(solution)

    def update_pheromones(self, solutions, pheromones):
        decay = 0.3
        for i in range(len(pheromones)):
            pheromones[i] *= (1 - decay)
        for solution, score in solutions:
            for c in solution:
                try:
                    index = solution.index(c)
                    pheromones[index] += score / 100.0
                except ValueError:
                    pass
        return pheromones

    async def verifica_matriz(self, respuestas, restricciones):
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
            output = await self.model.generate_content_async(prompt)

            if not output or not getattr(output, "text", None):
                raise ValueError("La salida del modelo está vacía o malformada")

            text = output.text.strip().replace("“", "\"").replace("”", "\"")

            # Intentar extraer bloque JSON con regex
            match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)

            # parsed = json.loads(text)
            parsed = extraer_respuestas_crudas(text)

            mapa = {}
            for obj in parsed:
                respuesta = obj.get("respuesta", "").strip()
                cumple = obj.get("cumple", [])
                for i, estado in enumerate(cumple):
                    key = (respuesta, restricciones[i])
                    mapa[key] = "sí" in estado.lower()
            return mapa

        except Exception as e:
            print(f"[ValidationAgent] Error en verifica_matriz:\n{e}")
            print(f"[ValidationAgent] Output del modelo:\n{getattr(output, 'text', '')}")
            return {(r, c): False for c in respuestas for r in restricciones}

    async def verifica_suficiencia(self, pregunta, respuestas, candidates, restricciones_grupales):
        campos_disponibles = [
            "Url", "Glass", "Ingredients", "Instructions",
            "Review", "History", "Nutrition", "Alcohol_Content", "Garnish"
        ]

        prompt = f"""
        You are a bartender assistant for answer questions about drinks. Given this consult:
        \"{pregunta}\"
        And the next answer:
        {json.dumps(respuestas, indent=2, ensure_ascii=False)}
        And these other candidates for answer:
        {json.dumps(candidates, indent=2, ensure_ascii=False)}
        We also have these information about all of our drinks: {campos_disponibles}
        Make a JSON like this:
        - "first answer": The answer as it is given to you.
        - "add-ons": Some of the candidates that helps to have enough data to accomplish these restrictions: {', '.join(restricciones_grupales)}. If the answer by itself already accomplish this, then this field should be empty.
        - "suficiente": True or False. Indicates if "first answer" and "add-ons" contains all the necesary data to give an apropiate basic answer, without the fields of information that are not mentioned about each drink of the answer.
        - "datos_locales_suficientes": True or False. Indicates if, having the drinks on "first answer" and "add-ons", if any of them requires one or more of the data fields that we have for each drink, that are not in the answer, for having information to give an apropiate answer. If "suficiente" is True, then this should be True.
        - "campos_requeridos": [drink1, [field1, field2,...]] In case that datos_locales_suficientes is True, what info is necessary about each drink that we must retrieve. It must contain the exact name of the drink, and all the required fields including the ones given on the answer.
        - "razonamiento": The reasoning behind your choices.
        """

        try:
            response = await self.model.generate_content_async(prompt)

            if not response or not getattr(response, "text", None):
                raise ValueError("La salida del modelo está vacía o malformada")

            raw_text = response.text
            cleaned = manual_json_extract(raw_text)

            return cleaned

        except Exception as e:
            print(f"[ValidationAgent] Error en verifica_suficiencia:\n{e}")
            print(f"[ValidationAgent] Output del modelo:\n{getattr(response, 'text', '')}")
            return {
                "first answer": respuestas[0] if respuestas else "",
                "add-ons": [],
                "suficiente": False,
                "se_puede_responder_con_datos_locales": True,
                "para cada trago elegido de respuesta, campos locales que deben extraerse para tener una respuesta completa": [],
                "razonamiento": "No se pudo interpretar la salida del modelo."
            }

    def stringify_candidate(self, candidate):
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
    campos = [
        "first answer",
        "add-ons",
        "suficiente",
        "datos_locales_suficientes",
        "campos requeridos",
        "razonamiento"
    ]

    resultado = {}

    pattern = '|'.join(re.escape(c) for c in campos)
    campo_regex = re.compile(rf'("({pattern})"\s*:\s*)', flags=re.IGNORECASE)

    posiciones = []
    for match in campo_regex.finditer(text):
        campo = match.group(2)
        inicio_valor = match.end()
        inicio_campo = match.start()
        posiciones.append((campo, inicio_valor, inicio_campo))

    posiciones.append(("__END__", len(text), len(text)))

    for i in range(len(posiciones) - 1):
        campo, inicio_valor, _ = posiciones[i]
        _, _, siguiente_campo = posiciones[i + 1]

        valor_bruto = text[inicio_valor:siguiente_campo].strip()
        if valor_bruto.endswith(','):
            valor_bruto = valor_bruto[:-1].strip()

        if campo == "campos requeridos":
            try:
                pares = re.findall(r'\[\s*"([^"]+)"\s*,\s*\[([^\]]+)\]\s*\]', valor_bruto)
                procesado = []
                for nombre, campos_str in pares:
                    campos_lista = [c.strip().strip('"') for c in campos_str.split(',')]
                    procesado.append(f"[{nombre}: {', '.join(campos_lista)}]")
                resultado[campo] = ', '.join(procesado)
            except Exception:
                resultado[campo] = "[Formato inválido]"

        elif campo in ["first answer", "add-ons"]:
            try:
                match_lista = re.search(r'\[(.*?)\]', valor_bruto, re.DOTALL)
                if match_lista:
                    json_raw = '[' + match_lista.group(1).strip() + ']'
                    json_raw = json_raw.replace("'", '"')
                    objetos = json.loads(json_raw)
                    representaciones = []
                    for item in objetos:
                        if isinstance(item, dict):
                            nombre = item.get("drink") or item.get("name")
                            if nombre:
                                representaciones.append(nombre)
                            else:
                                plano = ' '.join(f"{k} {v}" for k, v in item.items())
                                representaciones.append(plano)
                        elif isinstance(item, str):
                            representaciones.append(item.strip())
                        else:
                            representaciones.append(str(item))
                    resultado[campo] = ' | '.join(representaciones)
                else:
                    raise ValueError("No es lista válida")
            except Exception:
                # Fallback: texto plano sin intentar parsear
                valor_limpio = re.sub(r'[\n\r\t]', ' ', valor_bruto)
                valor_limpio = re.sub(r'[\{\}\[\]]', '', valor_limpio)
                valor_limpio = re.sub(r'\s+', ' ', valor_limpio)
                valor_limpio = valor_limpio.strip()
                resultado[campo] = valor_limpio
        else:
            valor_limpio = re.sub(r'[\n\r\t]', ' ', valor_bruto)
            valor_limpio = re.sub(r'[\[\]\{\}\"\'\:\,()]', '', valor_limpio)
            valor_limpio = re.sub(r'\s+', ' ', valor_limpio)
            valor_limpio = valor_limpio.strip()
            resultado[campo] = valor_limpio

    return resultado