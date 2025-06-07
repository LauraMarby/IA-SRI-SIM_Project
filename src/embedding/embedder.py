import json
import requests
import pickle
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer

# ==== Configuración ====
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

DATA_DIR = Path("src/data")
OUTPUT_FILE = Path("src/embedding/embeddings.pkl")

# ==== Funciones ====

def sliding_window_chunk(text: str, window_size: int = 100, stride: int = 60) -> List[str]:
    """
    Convierte el texto recibido en chunks(pedazos solapados de texto) 
    Args:
        text (str): Texto que se desea convertir en chunks
        window_size (int): Tamaño del chunk 
        stride (int): Tamaño del solapamiento
    Returns:
        List[str]: Lista de chunks
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), window_size - stride):
        chunk = " ".join(words[i:i + window_size])
        if len(chunk) > 10:
            chunks.append(chunk)
        if i + window_size >= len(words):
            break
    return chunks

def get_embedding(text:str):
    """ Computa un embedding para un texto dado utilizando el modelo sentence-transformers/all-MiniLM-L6-v2.
    Args:
        text (str): Texto para el cual se desea generar un embedding.
    Returns:
        list: Embedding del texto dado.
    """

    try:
        vector = model.encode(text)
        return vector
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el embedding: {e}")
        return None

def preprocess_document(json_file: Path) -> str:
    """
    Recopila el contenido del json en un str
    Args:
        json_file (Path): Dirección del documento a preprocesar
    Returns:
        str: Contenido del documento
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Caso original: un dict
            return " ".join(str(v) for v in data.values())
        elif isinstance(data, list):
            # Caso lista de dicts: concatenar todos los valores
            texts = []
            for entry in data:
                if isinstance(entry, dict):
                    texts.append(" ".join(str(v) for v in entry.values()))
                else:
                    texts.append(str(entry))
            return " ".join(texts)
        else:
            # Otro tipo de dato JSON
            return str(data)
    except Exception as e:
        print(f"❌ Error leyendo {json_file.name}: {e}")
        return ""

def embed_all_documents():
    """
    Carga todos los documentos en data y genera el embedding
    """
    embeddings = []
    for file in DATA_DIR.glob("*.json"):
        print(f"📄 Procesando: {file.name}")
        full_text = preprocess_document(file)
        chunks = sliding_window_chunk(full_text)
        for chunk in chunks:
            vector = get_embedding(chunk)
            if vector.any():
                embeddings.append({
                    "source": file.name,
                    "chunk": chunk,
                    "embedding": vector
                })
    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(embeddings, f)
    print(f"✅ Embeddings guardados en: {OUTPUT_FILE}")

# ==== Ejecución principal ====
if __name__ == "__main__":
    embed_all_documents()
