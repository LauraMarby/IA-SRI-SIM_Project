import os
import json
import random
from pathlib import Path
from ontology.query_ontology import consultar_tragos
from owlready2 import get_ontology, onto_path


def run_ontology(docs):

    # 1. Cargar Ontología
    ONTO_PATH = "src/ontology/ontology.owl"
    onto_path.append(os.path.dirname(ONTO_PATH))
    onto = get_ontology(ONTO_PATH).load()

    # 2. Cargar 1000 nombres aleatorios desde src/data/
    DATA_DIR = Path("src/data")
    json_files = list(DATA_DIR.glob("*.json"))
    random.shuffle(json_files)
    json_files = json_files[:docs]

    nombres = []
    for file in json_files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            nombres.append(data["Name"])
        except Exception as e:
            print(f"⚠️ Error leyendo {file.name}: {e}")

    # 3. Generar vectores aleatorios de campos (9 booleanos por nombre)
    NUM_CAMPOS = 9
    campos_por_nombre = [[random.choice([True, False]) for _ in range(NUM_CAMPOS)] for _ in nombres]

    # 4. Consultar ontología
    resultados = consultar_tragos(nombres, campos_por_nombre, onto)

    # 5. Validar resultados
    def validar_resultado(resultado, campos):
        nombre = resultado.get("Nombre", "")
        if "Error" in resultado:
            return [None] * NUM_CAMPOS  # No se puede validar

        checks = []
        checks.append("Url" in resultado if campos[0] else "Url" not in resultado)
        checks.append("Glass" in resultado if campos[1] else "Glass" not in resultado)
        checks.append("Ingredients" in resultado if campos[2] else "Ingredients" not in resultado)
        checks.append("Instructions" in resultado if campos[3] else "Instructions" not in resultado)
        checks.append("Review" in resultado if campos[4] else "Review" not in resultado)
        checks.append("History" in resultado if campos[5] else "History" not in resultado)
        checks.append("Nutrition" in resultado if campos[6] else "Nutrition" not in resultado)
        checks.append("Alcohol_Content" in resultado if campos[7] else "Alcohol_Content" not in resultado)
        checks.append("Garnish" in resultado if campos[8] else "Garnish" not in resultado)
        return checks

    # 6. Evaluar
    aciertos_por_campo = [0] * NUM_CAMPOS
    total_validos = 0
    errores = 0

    for campos, resultado in zip(campos_por_nombre, resultados):
        checks = validar_resultado(resultado, campos)
        if checks[0] is None:
            errores += 1
            continue
        total_validos += 1
        for i, ok in enumerate(checks):
            if ok:
                aciertos_por_campo[i] += 1

    # 7. Mostrar resultados
    print("\n✅ Resultados de validación de ontología:")
    nombres_campos = [
        "Url", "Glass", "Ingredients", "Instructions", "Review",
        "History", "Nutrition", "Alcohol_Content", "Garnish"
    ]

    for i, nombre_campo in enumerate(nombres_campos):
        porcentaje = (aciertos_por_campo[i] / total_validos) * 100 if total_validos else 0
        print(f"  - {nombre_campo:17}: {porcentaje:.2f}% campos correctos")

    print(f"\n🔢 Total de tragos válidos: {total_validos} / {len(nombres)}")
    print(f"❌ Errores de carga/consulta: {errores}")
