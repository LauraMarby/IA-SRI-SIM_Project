from embedding.embedder import get_embedding
import numpy as np

def retrieve(query: str, store_vectors, top_k=5):
    """
    Recupera los k textos más cercanos a la query según la distancia euclidiana.
    
    Args:
        query (str): query del usuario.
        store_vectors (List of dict): Cada embedding es un vector junto con su texto original y el archivo al que pertenece.
        top_k (int): Cantidad de textos a recuperar.
    Returns:
        List of str: Textos más cercanos a la query.
    """
    
    query_embedding = get_embedding(query)
    if query_embedding is None:
        return []
    
    distances = []
    for dict in store_vectors:
        distances.append((np.linalg.norm(query_embedding - dict["embedding"]), dict["chunk"]))

    distances.sort(key=lambda x: x[0])

    return [chunk for _, chunk in distances[:top_k]]