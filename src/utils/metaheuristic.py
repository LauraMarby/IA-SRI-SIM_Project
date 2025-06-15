import random
from collections import deque

class TabuSearchSelector:
    def __init__(self, alpha=10, beta=1, gamma=1, max_iters=100, tenure=10):
        self.alpha = alpha  # Peso restricciones fuertes
        self.beta = beta    # Peso restricciones débiles
        self.gamma = gamma  # Penalización por tamaño de solución
        self.max_iters = max_iters
        self.tenure = tenure
        self.all_candidates = []

    def select(self, candidates, restrictions, matriz):
        self.all_candidates = candidates
        num_fuertes = len(restrictions["fuertes"])
        num_debiles = len(restrictions["débiles"])

        # Estado inicial: uno aleatorio
        current = [random.randint(0, len(candidates)-1)]
        best = list(current)
        best_score = self.evaluate(current, matriz, num_fuertes, num_debiles)

        tabu_list = deque(maxlen=self.tenure)

        for _ in range(self.max_iters):
            neighborhood = self.generate_neighbors(current, len(candidates))
            best_neighbor = None
            best_neighbor_score = float("-inf")

            for neighbor in neighborhood:
                key = tuple(sorted(neighbor))
                if key in tabu_list:
                    continue

                score = self.evaluate(neighbor, matriz, num_fuertes, num_debiles)

                if score > best_neighbor_score:
                    best_neighbor_score = score
                    best_neighbor = neighbor

            if best_neighbor is not None:
                current = best_neighbor
                tabu_list.append(tuple(sorted(current)))

                if best_neighbor_score > best_score:
                    best = best_neighbor
                    best_score = best_neighbor_score

        return [candidates[i] for i in best], best_score

    def evaluate(self, indices, matriz, num_fuertes, num_debiles):
        if not indices:
            return float("-inf")

        cumples_f = [False] * num_fuertes
        cumples_d = [False] * num_debiles

        for idx in indices:
            vector = matriz[idx]
            for i in range(num_fuertes):
                cumples_f[i] |= vector[i]
            for j in range(num_debiles):
                cumples_d[j] |= vector[num_fuertes + j]

        score_f = sum(cumples_f)
        score_d = sum(cumples_d)

        return self.alpha * score_f + self.beta * score_d - self.gamma * len(indices)


    def generate_neighbors(self, current, total):
        neighbors = []

        # Agregar un nuevo índice no presente
        for i in range(total):
            if i not in current:
                neighbors.append(current + [i])

        # Quitar uno existente (si quedan al menos 1)
        if len(current) > 1:
            for i in current:
                new = [x for x in current if x != i]
                neighbors.append(new)

        return neighbors

