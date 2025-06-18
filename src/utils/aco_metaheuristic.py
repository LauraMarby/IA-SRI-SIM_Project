import random

all_candidates = []
max_iters = 20
num_ants = 10
alpha = 100
beta = 1
gamma = 2

def ant_colony_optimization(candidates, restrictions, matriz):
    global all_candidates, max_iters, num_ants, alpha, beta, gamma
    all_candidates = candidates  # ✅ Asignamos para uso global en esta instancia

    pheromones = [1.0] * len(candidates)
    best_solution = None
    best_score = float("-inf")
    seen_keys = set()

    try:
        for _ in range(max_iters):
            for _ in range(num_ants):
                solution = construct_solution(candidates, pheromones)

                # ⚠️ Normalizamos la solución: orden y sin repeticiones
                solution = sorted(set(solution), key=lambda x: str(x))
                key = tuple(solution)

                if key in seen_keys:
                    continue

                seen_keys.add(key)
                score = evaluate_fitness(solution, restrictions, matriz)

                if score > best_score:
                    best_score = score
                    best_solution = solution

            pheromones = update_pheromones(
                [([s for s in best_solution], best_score)] if best_solution else [],
                pheromones
            )

        if best_solution:
            return best_solution, best_score
        else:
            raise ValueError("No se encontró solución óptima")

    except Exception as e:
        print(f"[WARNING] Error en ACO: {e}")

        # Buscar un candidato que cumpla la mayoría de restricciones
        num_fuertes = len(restrictions["fuertes"])
        mejor_idx = None
        mejor_score = float("-inf")

        for idx, vector in enumerate(matriz):
            fuertes_cumplidas = sum(vector[:num_fuertes])
            debiles_cumplidas = sum(vector[num_fuertes:])
            score = alpha * fuertes_cumplidas + beta * debiles_cumplidas - gamma * 1

            if score > mejor_score:
                mejor_score = score
                mejor_idx = idx

        if mejor_idx is not None:
            return [candidates[mejor_idx]], mejor_score
        else:
            # Si ni siquiera eso se puede, devuelve el primero
            return [candidates[0]], -10000

def construct_solution(candidates, pheromones):
    num_to_select = min(5, len(candidates))
    total_pheromones = sum(pheromones)
    selected_indices = set()

    while len(selected_indices) < num_to_select:
        # Recalcular el total de feromonas solo de los disponibles
        available_indices = [i for i in range(len(candidates)) if i not in selected_indices]
        if not available_indices:
            break  # ya no hay más para seleccionar

        total_pheromones = sum(pheromones[i] for i in available_indices)
        r = random.uniform(0, total_pheromones)
        cumulative = 0.0

        for i in available_indices:
            cumulative += pheromones[i]
            if cumulative >= r:
                selected_indices.add(i)
                break

    return [candidates[i] for i in selected_indices]

def evaluate_fitness(solution, restrictions, matriz):
    fuertes = restrictions["fuertes"]
    debiles = restrictions["débiles"]

    # Índices de restricciones
    num_fuertes = len(fuertes)
    num_debiles = len(debiles)

    # Inicializamos vectores de cumplimiento conjunto
    cumples_f = [False] * num_fuertes
    cumples_d = [False] * num_debiles

    for cand in solution:
        try:
            idx = next((i for i, c in enumerate(all_candidates) if str(c) == str(cand)), None)
            if idx is None:
                continue
            vector = matriz[idx]
            for i in range(num_fuertes):
                cumples_f[i] = cumples_f[i] or vector[i]
            for j in range(num_debiles):
                cumples_d[j] = cumples_d[j] or vector[num_fuertes + j]
        except ValueError:
            continue  # Si por alguna razón el candidato no está

    # Ponderación: penaliza si no cumple todas las fuertes
    if not all(cumples_f):
        return -10000

    debiles_cumplidas = sum(cumples_d)
    return alpha * num_fuertes + beta * debiles_cumplidas - gamma * len(solution)

def update_pheromones(solutions, pheromones):
    decay = 0.3
    pheromones = [p * (1 - decay) for p in pheromones]

    for solution, score in solutions:
        for c in solution:
            try:
                idx = all_candidates.index(c)
                pheromones[idx] += score / 100.0
            except ValueError:
                pass
    return pheromones
