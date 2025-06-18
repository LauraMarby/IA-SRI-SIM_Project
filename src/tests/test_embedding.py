import json
import random
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

def run_embedding(n, m, i, j):

    # Cargar modelo de embedding
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Paso 1: Seleccionar n documentos JSON al azar de src/data/
    DATA_DIR = Path("src/data")
    json_files = list(DATA_DIR.glob("*.json"))
    random.shuffle(json_files)
    json_files = json_files[:n]

    # Paso 2: Extraer m fragmentos por documento
    fragmentos = []  # lista de tuplas: (fragmento, contexto_completo)
    fuentes = []

    for file in json_files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            text_fields = [v for k, v in data.items() if isinstance(v, str) and len(v.split()) > j]
            if not text_fields:
                continue
            for _ in range(m):
                base_text = random.choice(text_fields)
                words = base_text.split()
                if len(words) < j:
                    continue
                start = random.randint(0, len(words) - j)
                length = random.randint(i, j)
                fragment = " ".join(words[start:start + length])
                fragmentos.append(fragment)
                fuentes.append(base_text)
        except Exception as e:
            print(f"⚠️ Error leyendo {file.name}: {e}")

    # Paso 3: Generar preguntas en inglés con plantilla (simulación simple)
    preguntas = [f"What does the following text talk about: '{frag[:30]}...'" for frag in fragmentos]

    # Paso 4: Calcular embeddings y recuperar similaridad
    query_embeddings = model.encode(preguntas, convert_to_tensor=True)
    corpus_embeddings = model.encode(fuentes, convert_to_tensor=True)

    # Evaluar si el fragmento fue recuperado correctamente
    top_k = 5
    resultados = []
    for idx, (pregunta, frag, fuente) in enumerate(zip(preguntas, fragmentos, fuentes)):
        query_emb = query_embeddings[idx]
        cos_scores = util.cos_sim(query_emb, corpus_embeddings)[0]
        top_results = cos_scores.topk(k=top_k)
        indices_top = top_results.indices.tolist()
        retrieved = [fuentes[i] for i in indices_top]
        # Evaluaciones
        precision_top1 = frag in retrieved[0]
        precision_topk = any(frag in texto for texto in retrieved)
        resultados.append((precision_top1, precision_topk))

    # Paso 5: Mostrar métricas
    precision_1 = sum(1 for r in resultados if r[0]) / len(resultados)
    precision_k = sum(1 for r in resultados if r[1]) / len(resultados)

    print("\n\n✅ Resultados de validación de embedding:")
    print(f"🔎 Total evaluaciones: {len(resultados)}")
    print(f"🎯 Precisión en top-1: {precision_1:.2%}")
    print(f"📚 Precisión en top-{top_k}: {precision_k:.2%}")
