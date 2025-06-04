import random
import asyncio
from agents.base_agent import BaseAgent

class ValidationAgent(BaseAgent):
    def __init__(self, name, system, model, alpha=100, beta=1, gamma=2, num_ants=10, max_iters=20):
        super().__init__(name, system)
        self.model = model
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.num_ants = num_ants
        self.max_iters = max_iters

    async def run(self):
        while True:
            msg = await self.receive()
            query = msg["query"]
            candidates = msg["candidates"]  # lista de respuestas [{"text": ..., ...}, ...]
            sender = msg["from"]

            restrictions = await self.extract_constraints(query, candidates)
            selected = self.ant_colony_optimization(candidates, restrictions)
            explanation = self.explain(selected, restrictions)

            await self.send(sender, {
                "respuestas_validadas": selected,
                "explicacion": explanation
            })

    async def extract_constraints(self, query, candidates):
        prompt = f"""
Dada esta consulta de usuario: \"{query}\"
y las siguientes respuestas candidatas:
{[c['text'][:200] for c in candidates]}

Extrae las restricciones que debe cumplir una respuesta válida.
Clasifica cada una como fuerte (obligatoria) o débil (deseable).

Devuelve en formato JSON con dos listas: restricciones_fuertes, restricciones_debiles.
"""
        response = await self.model.generate_content_async(prompt)
        try:
            json_text = response.text.strip('`\n')
            return eval(json_text)  # reemplazar por json.loads si formato es seguro
        except Exception as e:
            print(f"[ValidationAgent] Error parsing restricciones: {e}")
            return {"restricciones_fuertes": [], "restricciones_debiles": []}

    def ant_colony_optimization(self, candidates, restrictions):
        pheromones = [1.0] * len(candidates)
        best_solution = None
        best_score = float('-inf')

        for _ in range(self.max_iters):
            solutions = []
            for _ in range(self.num_ants):
                solution = self.construct_solution(candidates, pheromones, restrictions)
                score = self.evaluate_fitness(solution, restrictions)
                solutions.append((solution, score))

                if score > best_score:
                    best_score = score
                    best_solution = solution

            pheromones = self.update_pheromones(solutions, pheromones)

        return best_solution

    def construct_solution(self, candidates, pheromones, restrictions):
        solution = []
        for i, c in enumerate(candidates):
            p = pheromones[i] * random.uniform(0.5, 1.5)
            if random.random() < p / (p + 1):
                solution.append(c)
        return solution

    def evaluate_fitness(self, solution, restrictions):
        fuertes = restrictions["restricciones_fuertes"]
        debiles = restrictions["restricciones_debiles"]

        def cumple(rest, s):
            # Aquí puedes usar una mejor métrica semántica
            return all(any(r.lower() in c['text'].lower() for c in s) for r in rest)

        if not cumple(fuertes, solution):
            return float('-inf')

        debiles_cumplidas = sum(
            1 for r in debiles if any(r.lower() in c['text'].lower() for c in solution)
        )

        return self.alpha * len(fuertes) + self.beta * debiles_cumplidas - self.gamma * len(solution)

    def update_pheromones(self, solutions, pheromones):
        decay = 0.3
        for i in range(len(pheromones)):
            pheromones[i] *= (1 - decay)
        for solution, score in solutions:
            for i, c in enumerate(solution):
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
