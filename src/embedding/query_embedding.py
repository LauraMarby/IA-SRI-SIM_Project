from embedding.embedder import get_embedding
import numpy as np

def retrieve(query_list: list[str], store_vectors, top_k=5):
    """
    Recupera los k textos más cercanos a cada query según la distancia euclidiana.

    Args:
        query_list (List[str]): Lista de queries del usuario.
        store_vectors (List[dict]): Cada embedding es un vector junto con su texto original y el archivo al que pertenece.
        top_k (int): Cantidad de textos a recuperar por cada query.

    Returns:
        List[str]: Conjunto total de textos más cercanos a todas las queries.
    """
    results = []

    for query in query_list:
        query_embedding = get_embedding(query)
        if query_embedding is None:
            continue

        distances = []
        for item in store_vectors:
            dist = np.linalg.norm(query_embedding - item["embedding"])
            distances.append((dist, item["chunk"]))

        distances.sort(key=lambda x: x[0])
        top_chunks = [chunk for _, chunk in distances[:top_k]]
        results.extend(top_chunks)

    return results
