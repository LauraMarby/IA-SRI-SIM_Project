import random
from utils.aco_metaheuristic import ant_colony_optimization  # Asegúrate de tener estos agentes implementados
from utils.metaheuristic import TabuSearchSelector

def test_aco_vs_tabu_multiple_seeds():
    seeds = list(range(500))
    victories_tabu = 0
    victories_aco = 0
    empate = 0

    scores_aco = []
    scores_tabu = []

    for seed in seeds:
        random.seed(seed)

        num_candidates = 10
        num_fuertes = 3
        num_debiles = 2

        candidates = [f"Cocktail_{i}" for i in range(num_candidates)]
        matriz = [
            [random.choice([0, 1]) for _ in range(num_fuertes + num_debiles)]
            for _ in range(num_candidates)
        ]

        restrictions = {
            "fuertes": [f"F{i}" for i in range(num_fuertes)],
            "débiles": [f"D{i}" for i in range(num_debiles)],
        }

        alpha, beta, gamma = 100, 1, 2

        # Ejecutamos ACO
        solution_aco, score_aco = ant_colony_optimization(candidates, restrictions, matriz)

        # Ejecutamos Tabu Search
        tabu = TabuSearchSelector(alpha=alpha, beta=beta, gamma=gamma, max_iters=20)
        solution_tabu, score_tabu = tabu.select(candidates, restrictions, matriz)

        scores_aco.append(score_aco)
        scores_tabu.append(score_tabu)

        if score_tabu > score_aco:
            victories_tabu += 1
        elif score_aco > score_tabu:
            victories_aco += 1
        else:
            empate += 1

        print(f"[Seed {seed}] ACO → {score_aco:.2f}, Tabu → {score_tabu:.2f}")

    print("\nResumen:")
    print(f"Tabu ganó en {victories_tabu} casos")
    print(f"ACO ganó en {victories_aco} casos")
    print(f"Empates: {empate}")
    print(f"Promedio ACO:  {sum(scores_aco)/len(scores_aco):.2f}")
    print(f"Promedio Tabu: {sum(scores_tabu)/len(scores_tabu):.2f}")
