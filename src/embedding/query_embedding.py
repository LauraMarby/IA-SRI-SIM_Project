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

# def rag_system(query, store_vectors):
#     """
#     Función que implementa un sistema de Generación Aumentada por Recuperación (RAG)
    
#     Args:
#         query (str): La consulta.
#         store_vectors (List of dict): Cada embedding es un vector junto con su texto original y el archivo al que pertenece.
        
#     Returns:
#         str: Respuesta generada por el modelo de lenguaje
#     """
    
#     fragments = retrieve(query, store_vectors)
#     # print(f"fragments found: {fragments}")

#     prompt = f"""Responde la siguiente pregunta basándote en los fragmentos de texto proporcionados. 
#     No digas frases como: "basado en la información que me diste...", "el texto dice...", "de las recetas proporcionadas...", responde la pregunta del usuario.
#     Si no logras encontrar una respuesta válida, inventate la respuesta.

#     Fragmentos:
#     {chr(10).join(f"- {frag}" for frag in fragments)}

#     Pregunta del usuario: {query}
#     """

#     answer = generate(prompt)

#     return answer


# # API Key para la API de Google Gemini
# GEMINI_API_KEY = ""

# def generate(message): 
#     """
#     Generador de respuesta para el modelo de lenguaje

#     Args:
#         message (str): mensaje a enviar al modelo
#     Returns:
#         str: Respuesta del modelo  
#     """  

#     genai.configure(api_key=GEMINI_API_KEY)
#     model = genai.GenerativeModel('gemini-1.5-flash')
#     response = model.generate_content(message)
            
#     return response.text