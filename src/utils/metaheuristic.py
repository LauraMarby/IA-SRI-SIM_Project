from collections import deque

class TabuSearchRestricciones:
    def __init__(self, max_iters=200, tabu_size=100):
        self.max_iters = max_iters
        self.tabu_size = tabu_size

    def optimize(self, candidates, fuertes, debiles, matriz):
        self.candidates = candidates
        self.fuertes = fuertes
        self.debiles = debiles
        self.matriz = matriz

        # Crear diccionario de mapeo claro entre texto y vector de cumplimiento
        self.matriz_dict = {}
        for i, cand in enumerate(candidates):
            vector = matriz[i]
            fuertes_vec = vector[:len(fuertes)]
            debiles_vec = vector[len(fuertes):]
            self.matriz_dict[cand] = {
                "fuertes": fuertes_vec,
                "debiles": debiles_vec
            }

        current = self.greedy_initial_solution()
        best = current[:]
        best_score = self.evaluate(best)

        tabu = deque(maxlen=self.tabu_size)
        tabu.append(self._hash(best))

        for _ in range(self.max_iters):
            neighbors = self.generate_neighbors(current)
            valid = [n for n in neighbors if self._hash(n) not in tabu and self.valid(n)]

            if not valid:
                break

            next_solution = min(valid, key=lambda x: (-self.evaluate(x), len(x)))
            next_score = self.evaluate(next_solution)

            if next_score > best_score or (next_score == best_score and len(next_solution) < len(best)):
                best = next_solution[:]
                best_score = next_score

            tabu.append(self._hash(next_solution))
            current = next_solution

        return best, best_score

    def _hash(self, sol):
        return tuple(sorted(sol))

    def valid(self, sol):
        """Verifica que todas las fuertes estén cubiertas por al menos un candidato."""
        cubiertas = set()
        for s in sol:
            cumplimiento = self.matriz_dict.get(s, {}).get("fuertes", [])
            for f, ok in zip(self.fuertes, cumplimiento):
                if ok:
                    cubiertas.add(f)
        return len(cubiertas) == len(self.fuertes)

    def greedy_initial_solution(self):
        """Selecciona candidatos que cubran todas las fuertes con el mínimo posible."""
        cubiertas = set()
        seleccion = set()

        while cubiertas < set(self.fuertes):
            mejor = None
            mejor_gain = 0
            for c in self.candidates:
                cumplimiento = self.matriz_dict.get(c, {}).get("fuertes", [])
                gain = sum(
                    1 for f, ok in zip(self.fuertes, cumplimiento)
                    if ok and f not in cubiertas
                )
                if gain > mejor_gain:
                    mejor = c
                    mejor_gain = gain
            if mejor is None:
                break
            seleccion.add(mejor)
            cumplimiento = self.matriz_dict.get(mejor, {}).get("fuertes", [])
            cubiertas |= {f for f, ok in zip(self.fuertes, cumplimiento) if ok}

        return list(seleccion)

    def generate_neighbors(self, sol):
        vecinos = []

        # Intentar quitar elementos
        if len(sol) > 1:
            for i in range(len(sol)):
                nuevo = sol[:i] + sol[i+1:]
                vecinos.append(nuevo)

        # Intentar cambiar un fragmento
        for i in range(len(sol)):
            for c in self.candidates:
                if c not in sol:
                    nuevo = sol[:i] + [c] + sol[i+1:]
                    vecinos.append(nuevo)

        # Intentar agregar uno más
        for c in self.candidates:
            if c not in sol:
                vecinos.append(sol + [c])

        return vecinos

    def evaluate(self, sol):
        """Cuenta cuántas restricciones débiles se cumplen en total."""
        cubiertas_d = set()
        for s in sol:
            cumplimiento = self.matriz_dict.get(s, {}).get("debiles", [])
            for d, ok in zip(self.debiles, cumplimiento):
                if ok:
                    cubiertas_d.add(d)
        return len(cubiertas_d)
