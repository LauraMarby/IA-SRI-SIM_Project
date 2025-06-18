from tests.test_ontology import run_ontology
from tests.test_embedding import run_embedding
from tests.test_flavor import run_flavor, generar_formulas
from agents.flavor_agent import Flavor_Agent
from ontology.query_ontology import consultar_tragos
from tests.test_metaheuristic import test_aco_vs_tabu_multiple_seeds
import json

# Ejecutando búsqueda en la ontología con campos aleatorios para 1000 documentos aleatorios
run_ontology(1000)

# Ejecutando búsqueda en el embedding con 100 documentos aleatorios, 5 fragmentos por documento de entre 15-20 palabras
run_embedding(100, 10, 15, 20)

# Ejecutando test para agente de sabores
# Crear agente
agente = Flavor_Agent("flavor", None, consultar_tragos)
# Cargar vectores de sabor
DATA_FILE = "src/flavor_space/cocktail_flavor_vectors.json"
with open(DATA_FILE, "r", encoding="utf-8") as f:
    flavor_vectors = json.load(f)
# Generar fórmulas aleatorias
formulas = generar_formulas(30)  # puedes ajustar el número
# Ejecutar evaluación del agente de sabor
run_flavor(agente, formulas, flavor_vectors, k=5)


test_aco_vs_tabu_multiple_seeds()

# ✅ ¿Por qué ACO siempre da 292?
# 1. Fitness está altamente dominado por alpha
# return alpha * num_fuertes + beta * debiles_cumplidas - gamma * len(solution)
# Con alpha = 100, num_fuertes = 3:

# score_base = 100 * 3 = 300
# La penalización máxima por tamaño (len(solution)) es -gamma * 5 = -10

# El aporte de las débiles (beta * debiles_cumplidas) es como mucho +2

# ➡️ Resultado típico:
# fitness = 300 + [0..2] - [1..10] ⇒ ~292
# 📌 Conclusión: El valor 292 aparece porque es el fitness de una solución de 5 elementos, que cumple todas las fuertes y pocas débiles. Y como todas las soluciones válidas tienden a eso, se estanca ahí.

# 2. Exploración débil debido al uso único de best_solution
# pheromones = update_pheromones(
#     [([s for s in best_solution], best_score)] if best_solution else [],
#     pheromones
# )
# Sólo se actualizan las feromonas con la mejor solución histórica

# Esto hace que no haya diversidad: si una solución se encontró primero, se refuerza ciegamente, aunque no sea óptima
# 📌 ACO debería usar varias soluciones buenas (por iteración), no solo la mejor global.

# 3. Baja presión de selección y sin uso de heurística
# No usas heurística (η o visibilidad) para guiar la probabilidad de selección.

# Solo feromonas → comportamiento casi aleatorio, especialmente al principio.

# 4. Uso de seen_keys limita aún más la diversidad
# if key in seen_keys:
#     continue
# Evita repetir combinaciones, pero combinado con la baja variedad de construcción, hace que se ignoren muchas oportunidades válidas.