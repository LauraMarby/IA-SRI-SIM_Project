import numpy as np
from typing import List, Tuple, Any

def softmax(tuples: List[Tuple[Any, float]], T=0.5) -> List[Tuple[Any, float]]:
    """
    Algoritmo softmax para generar una distribución entre cocteles que define qué 
    coctel tiene más probabilidades de ser escogido.
    
    Args:
        tuples: Lista de tuplas donde el segundo elemento es el valor float
        T: Parámetro de temperatura para softmax
    
    Returns:
        Lista de tuplas con los mismos primeros elementos pero con segundos elementos normalizados
    """
    flavors = [value for _, value in tuples]
    
    exp_values = np.exp(np.array(flavors)/T)
    normalized_flavors = exp_values / np.sum(exp_values)
    
    return [(item[0], norm_value) for item, norm_value in zip(tuples, normalized_flavors)]

def select_k_without_replace(tuples: List[Tuple[Any, float]], k: int) -> List[Tuple[Any, float]]:
    """
    Selecciona k tuplas distintas según las probabilidades dadas por los segundos elementos
    
    Args:
        tuples: Lista de tuplas donde el segundo elemento es el valor de probabilidad/peso
        k: Número de elementos a seleccionar (sin repetición)
    
    Returns:
        Lista con las tuplas seleccionadas
    """
    vector_prob = [value for _, value in tuples]
    
    prob = np.array(vector_prob, dtype=float)
    prob = prob / prob.sum() 
    
    if k <= 0:
        return []
    if k > len(prob):
        raise ValueError("k no puede ser mayor que el número de elementos")
    
    seleccionados = np.random.choice(
        len(prob),
        size=k,
        p=prob,
        replace=False
    )
    
    return [tuples[i] for i in seleccionados]

# tuples = [("cocktail1", 1.5), ("cocktail2", 2.0), ("cocktail3", 0.5)]

# # Aplicar softmax
# normalized = softmax(tuples)
# print(normalized)

# # Seleccionar 2 elementos
# selected = select_k_without_replace(normalized, 2)
# print(selected)