import random
from agents.base_agent import BaseAgent
import json
import re
import asyncio

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
            results = content.get("results")

            if source:
                self.received_data[source] = results

            if self.expected_sources.issubset(self.received_data.keys()):
                candidates = self.received_data.get("embedding", [])
                restrictions = await self.extract_constraints(self.query, candidates)
                selected = await self.ant_colony_optimization(candidates, restrictions)
                explanation = self.explain(selected, restrictions)

                # ⚠️ Verificación de suficiencia con el modelo de lenguaje
                suficiencia = await self.verifica_suficiencia(self.query, selected, restrictions["restricciones_fuertes_conjuntas"])

                await self.send("coordinator", suficiencia)

    async def extract_constraints(self, query, candidates):
        prompt = f"""
Eres un asistente para procesar consultas de usuarios sobre cocteles y tragos. Dada esta consulta de usuario: \"{query}\"
y las siguientes respuestas candidatas:
{[c[:200] for c in candidates]}

Extrae las restricciones que debe cumplir una respuesta válida.
Clasifica cada una en tres categorías:
- restricciones_fuertes: obligatorias que debe cumplir cada respuesta individual.
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
        all_solutions = {}

        for _ in range(self.max_iters):
            for _ in range(self.num_ants):
                solution = self.construct_solution(candidates, pheromones, restrictions)

                # Aseguramos que sea hashable y orden-insensible
                key = frozenset(solution)
                score = await self.evaluate_fitness(solution, restrictions, verificados)

                # Guardar solo el mejor score para cada conjunto único
                if key not in all_solutions or score > all_solutions[key]:
                    all_solutions[key] = score

            pheromones = self.update_pheromones(
                [(list(s), sc) for s, sc in all_solutions.items()],
                pheromones
            )

        # Convertir a lista de soluciones únicas y ordenarlas por score
        sorted_solutions = sorted(
            [(sorted(list(s), key=lambda x: str(x)), sc) for s, sc in all_solutions.items()],
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_solutions  # Lista de tuplas: [(solución_ordenada, score), ...]

    def construct_solution(self, candidates, pheromones, restrictions):
        solution = []
        for i, c in enumerate(candidates):
            p = pheromones[i] * random.uniform(0.5, 1.5)
            if random.random() < p / (p + 1):
                solution.append(c)
        return solution

    async def evaluate_fitness(self, solution, restrictions, verificados):
        fuertes = restrictions["restricciones_fuertes"]
        debiles = restrictions["restricciones_debiles"]

        # Validar fuertes individuales
        for r in fuertes:
            if not any(verificados.get((c, r), False) for c in solution):
                return float('-inf')

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

    def explain(self, respuestas, restrictions):
        return (
            f"Se seleccionaron {len(respuestas)} respuestas que cumplen con todas las restricciones fuertes: "
            f"{restrictions['restricciones_fuertes']} y cumplen o maximizan las débiles: "
            f"{restrictions['restricciones_debiles']}"
        )
    
    async def verifica_matriz(self, respuestas, restricciones):
        prompt = f"""
Tenemos una lista de respuestas candidatas y una lista de restricciones.

Para cada respuesta, indica si cumple cada restricción (sí o no). 

Responde en formato JSON como una lista de objetos, uno por respuesta. 
Cada objeto debe tener esta estructura: 
{{"respuesta": "texto", "cumple": ["sí", "no", "sí", ...]}}

Respuestas:
{json.dumps(respuestas[:200], ensure_ascii=False)}  # limitar para no pasar tokens

Restricciones:
{json.dumps(restricciones, ensure_ascii=False)}
"""

        output = await self.model.generate_content_async(prompt)

        try:
            text = output.text.strip()
            match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
            text = text.replace("“", "\"").replace("”", "\"")
            parsed = json.loads(text)

            mapa = {}
            for obj in parsed:
                respuesta = obj["respuesta"]
                for i, estado in enumerate(obj["cumple"]):
                    mapa[(respuesta, restricciones[i])] = "sí" in estado.lower()

            return mapa

        except Exception as e:
            print(f"[ValidationAgent] Error parsing verificación:\n{output.text}\n{e}")
            return {(r, c): False for c in respuestas for r in restricciones}

    async def verifica_suficiencia(self, pregunta, respuestas, restricciones_grupales):
        campos_disponibles = [
            "Url", "Glass", "Ingredients", "Instructions",
            "Review", "History", "Nutrition", "Alcohol_Content", "Garnish"
        ]

        prompt = f"""
Eres un asistente para procesar consultas de usuarios sobre cocteles y tragos. Dada la siguiente pregunta de usuario:

\"{pregunta}\"

Y la(s) siguiente(s) respuesta(s) obtenidas del sistema:

{json.dumps(respuestas, indent=2, ensure_ascii=False)}

Evalúa lo siguiente:

1. La primera respuesta cumple las siguientes restricciones: {', '.join(campos_disponibles)}?
En caso que no, verifique si se pueden cumplir estas restricciones agregando elementos de otras respuestas y detente cuando lo logres. Considera los agregados como add-ons
2. ¿Se puede responder completamente la pregunta con estas respuestas y sus add-ons? (sí o no).
3. Si no es suficiente, ¿se podría haber respondido si tuviéramos todos estos campos disponibles por trago?
Campos por documento:
{', '.join(campos_disponibles)}
Ten en cuenta solo los campos indispensables para la respuesta a la pregunta, no te extiendas más de lo necesario.

4. Da un razonamiento final en lenguaje natural.

Responde en formato JSON con estas claves:
- "first answer": respuesta inicial
- "add-ons": lista de agregados a la respuesta inicial
- "suficiente": true/false
- "se_puede_responder_con_datos_locales": true/false
- "para cada trago elegido de respuesta, campos locales que deben extraerse para tener una respuesta completa": [[trago1, [campo1, campo2...], [trago2, [campo1, campo2, campo 3...]]]]
- "razonamiento": string

Ten en cuenta que el usuario va a preguntar sobre tragos. Asume eso exccepto cuando se especifique explícitamente lo contrario en la consulta.
"""

        response = await self.model.generate_content_async(prompt)

        try:
            text = response.text.strip()
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)

            text = text.replace("“", "\"").replace("”", "\"")
            parsed = json.loads(text)
            return parsed

        except Exception as e:
            print(f"[ValidationAgent] Error parsing verificación de suficiencia:\n{response.text}\n{e}")
            return {
                "suficiente": False,
                "se_puede_responder_con_datos_locales": True,
                "razonamiento": "No se pudo interpretar la salida del modelo."
            }