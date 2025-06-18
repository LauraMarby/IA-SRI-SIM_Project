import os
import json
import random
import time
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from pydantic import BaseModel
import google.generativeai as genai
import re
from difflib import SequenceMatcher
import logging

# === CONFIGURACIÓN MEJORADA ===
def load_all_api_keys(path="src/tests/tokens.txt") -> List[str]:
    if not os.path.exists(path):
        print(f"❌ Archivo no encontrado: {path}")
        exit(1)

    with open(path, "r", encoding="utf-8") as f:
        keys = [line.strip() for line in f if line.strip()]

    if not keys:
        print("❌ El archivo de API keys está vacío")
        exit(1)

    print(f"✅ {len(keys)} API keys cargadas desde {path}")
    return keys


# Cargar todas las API keys disponibles
ALL_API_KEYS = load_all_api_keys()
current_api_key_index = 0
API_KEY = ALL_API_KEYS[current_api_key_index]

# Configuración de directorios y límites
DATA_DIR = Path("src/data")
DAILY_LIMIT = 500
RPM_LIMIT = 60  # Aumentado para permitir más peticiones
TPM_LIMIT = 250_000
REQUEST_LOG = "requests_today.txt"
STATS_FILE = "logs/stats_summary.json"
DETAIL_FILE = "logs/stats_details.json"
RETRY_LIMIT = 5
MAX_RUN_TIME = 30 * 60  # 30 minutos en segundos
TOKEN_BUDGET = 10000  # Presupuesto de tokens aumentado

# Inicializar directorios y archivos
os.makedirs("logs", exist_ok=True)

# Borrar y recrear archivos JSON vacíos
for file_path in [STATS_FILE, DETAIL_FILE]:
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2) if "summary" in file_path else json.dump([], f, indent=2)

# Configurar logging
logging.basicConfig(filename='logs/execution.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# === MODELO PYDANTIC ===
class CocktailData(BaseModel):
    Url: str
    Name: str
    Glass: str
    Ingredients: List[str]
    Instructions: List[str]
    Review: str
    History: str
    Nutrition: str
    Alcohol_Content: List[List[str]]
    Garnish: str

# === GESTIÓN DE API KEYS ===
def switch_api_key():
    global current_api_key_index, API_KEY, requests_today, requests_this_minute
    current_api_key_index += 1
    
    if current_api_key_index >= len(ALL_API_KEYS):
        print("⚠️ No hay más API keys disponibles")
        return False
        
    API_KEY = ALL_API_KEYS[current_api_key_index]
    genai.configure(api_key=API_KEY)
    requests_today = 0
    requests_this_minute = 0
    print(f"🔄 Cambiando a API_KEY {current_api_key_index+1}")
    logging.info(f"Cambiando a API_KEY {current_api_key_index+1}")
    return True

# === CONTROL DE PETICIONES MEJORADO ===
requests_today = 0
if os.path.exists(REQUEST_LOG):
    with open(REQUEST_LOG) as f:
        requests_today = int(f.read().strip())

requests_this_minute = 0
last_minute = time.time()
tokens_used = 0

def wait_if_needed():
    global requests_this_minute, last_minute
    now = time.time()
    elapsed = now - last_minute
    
    # Reiniciar contador si ha pasado más de 1 minuto
    if elapsed >= 60:
        requests_this_minute = 0
        last_minute = now
    elif requests_this_minute >= RPM_LIMIT:
        sleep_time = 60 - elapsed
        print(f"⏳ Límite RPM alcanzado. Esperando {sleep_time:.1f} segundos...")
        logging.warning(f"Límite RPM alcanzado. Esperando {sleep_time:.1f} segundos")
        time.sleep(sleep_time)
        requests_this_minute = 0
        last_minute = time.time()

def call_model(prompt: str) -> str:
    global requests_today, requests_this_minute, tokens_used
    
    retries = 0
    while retries < RETRY_LIMIT * 2:  # Más reintentos
        # Verificar límites antes de cada intento
        if requests_today >= DAILY_LIMIT:
            if not switch_api_key():
                return None
        
        wait_if_needed()
        
        try:
            response = gemini_model.generate_content(prompt)
            requests_this_minute += 1
            requests_today += 1
            
            # Estimación de tokens más precisa
            token_count = len(prompt.split()) + len(response.text.split())
            tokens_used += token_count
            
            # Actualizar archivo de contador
            with open(REQUEST_LOG, "w") as f:
                f.write(str(requests_today))
                
            return response.text
            
        except Exception as e:
            logging.error(f"Error en la API: {str(e)}")
            retries += 1
            wait_time = min(2 ** retries, 60)  # Espera exponencial con máximo 60 segundos
            print(f"⛔ Error: {str(e)}. Reintentando en {wait_time} segundos...")
            time.sleep(wait_time)
    
    print("⚠️ Reintentos agotados para esta petición")
    logging.error("Reintentos agotados para petición")
    return None

# === FUNCIONES DE DATOS MEJORADAS ===
def get_non_empty_fields(data: CocktailData) -> List[Tuple[str, str]]:
    """Obtiene campos no vacíos con sus valores convertidos a string"""
    fields = [
        ("Nombre", data.Name),
        ("Vaso", data.Glass),
        ("Ingredientes", data.Ingredients),
        ("Instrucciones", data.Instructions),
        ("Reseña", data.Review),
        ("Historia", data.History),
        ("Nutrición", data.Nutrition),
        ("Contenido_alcohólico", data.Alcohol_Content),
        ("Decoración", data.Garnish)
    ]
    
    non_empty = []
    for name, value in fields:
        if isinstance(value, list):
            # Manejar listas anidadas como Alcohol_Content
            if value and isinstance(value[0], list):
                flat_values = [f"{item[0]}: {item[1]}" for sublist in value for item in sublist]
                str_value = ". ".join(flat_values)
            else:
                str_value = ". ".join(map(str, value))
        elif isinstance(value, str):
            str_value = value.strip()
        else:
            str_value = str(value)
        
        if str_value:
            non_empty.append((name, str_value))
    
    return non_empty

def select_fields_for_stage(data: CocktailData, stage: int) -> Optional[List[Tuple[str, str]]]:
    """Selecciona campos para una etapa específica, manejando campos vacíos"""
    non_empty_fields = get_non_empty_fields(data)
    required_count = {
        1: 2, 2: 3, 3: 5, 4: 9, 5: 5, 6: 9
    }.get(stage, 2)
    
    # Para etapas que requieren todos los campos
    if stage in [4, 6]:
        if len(non_empty_fields) < required_count:
            logging.warning(f"Faltan campos para etapa {stage}: {len(non_empty_fields)}/{required_count}")
            return None
        return non_empty_fields
    
    # Para otras etapas, seleccionar aleatoriamente
    if len(non_empty_fields) < required_count:
        return None
    
    return random.sample(non_empty_fields, required_count)

def build_prompt_adaptive(stage: int, batch: List[Tuple[List[Tuple[str, str]], List[int]]]) -> str:
    """Builds the prompt with clear English instructions and examples"""
    stage_instructions = {
        1: "Generate a question based on ONE base fact that requires the target fact to answer.",
        2: "Generate a question based on ONE base fact that requires the TWO target facts to answer.",
        3: "Generate a question based on TWO base facts that requires the THREE target facts to answer.",
        4: "Generate a question based on THREE base facts that requires the SIX target facts to answer.",
        5: "Generate a question based on ONE base fact that requires the FOUR target facts to answer.",
        6: "Generate a question based on ONE base fact that requires the EIGHT target facts to answer."
    }
    
    header = f"""You are a cocktail expert. Your task is to generate questions about cocktails based on provided facts.

Instructions:
- Each entry contains base facts (to use in the question) and target facts (to answer)
- {stage_instructions[stage]}
- The question MUST require all target facts to be answered correctly
- DO NOT mention the target facts directly in the question
- The answer should be exactly the combined target facts
- Generate EXACTLY one question per entry, without numbering or prefixes

Examples:
* Stage 1:
  Base: Name: Mojito
  Target: Ingredients: Lime, mint, rum, sugar
  Question: What ingredients are needed to prepare a Mojito?

* Stage 3:
  Base: History: Created in 1997. Alcohol_Content: 1.3 standard drinks
  Target: Review: Jorge says it's good. Nutrition: 130 calories. Ingredients: Pineapple, chocolate, lemon
  Question: What are Jorge's reviews, the nutritional value and ingredients of a cocktail created in 1997 with 1.3 standard drinks of alcohol?

Now generate questions for the following entries:
"""
    
    body = []
    for i, (fields, base_indices) in enumerate(batch):
        base_facts = [f"{name}: {value}" for idx, (name, value) in enumerate(fields) if idx in base_indices]
        target_facts = [f"{name}: {value}" for idx, (name, value) in enumerate(fields) if idx not in base_indices]
        
        entry = f"Entry {i+1}:\n"
        entry += "Base facts:\n" + "\n".join(base_facts) + "\n"
        entry += "Target facts:\n" + "\n".join(target_facts)
        body.append(entry)
    
    return header + "\n\n".join(body) + "\n\nQuestions:\n"

def extract_questions(response: str) -> List[str]:
    """Extrae preguntas de la respuesta del modelo de forma robusta"""
    if not response:
        return []
    
    # Dividir por líneas y limpiar
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    
    # Filtrar líneas que parecen preguntas
    questions = []
    for line in lines:
        # Ignorar encabezados y numeración
        if line.lower().startswith(("pregunta", "entrada", "1.", "2.", "3.", "4.", "5.", "-", "*")):
            continue
        
        # Considerar como pregunta si contiene signo de interrogación o tiene suficiente longitud
        if '?' in line or len(line) > 20:
            # Limpiar prefijos numéricos
            clean_line = re.sub(r'^\d+[\.\)]\s*', '', line)
            questions.append(clean_line)
    
    return questions

def generate_response(question: str, expected: str) -> str:
    """Genera una respuesta simulada con diferentes niveles de precisión"""
    r = random.random()
    words = expected.split()
    
    if r < 0.6:
        return expected  # Respuesta correcta
    elif r < 0.85 and len(words) > 1:
        # Respuesta parcialmente correcta (falta algún detalle)
        return " ".join(random.sample(words, max(1, len(words)//2)))
    else:
        # Respuesta incorrecta
        return "Información no disponible" if random.random() < 0.5 else " ".join(random.sample(words, len(words)))

def get_response(question):
    pass

def get_true_correct(question: str, answer: str) -> dict:
    """
    Evalúa si una respuesta responde adecuadamente a una pregunta usando un modelo de lenguaje.
    
    Args:
        question (str): La pregunta original
        answer (str): La respuesta a evaluar
    
    Returns:
        dict: JSON con {'is_correct': bool} y detalles adicionales
    """
    # Construimos el prompt para el modelo evaluador
    prompt = f"""Eres un evaluador experto. Determina si la siguiente respuesta responde COMPLETAMENTE 
    y de manera CORRECTA a la pregunta. Considera:
    - La respuesta debe cubrir todos los aspectos de la pregunta
    - Debe ser factualmente correcta
    - No debe contener información irrelevante

    Responde ÚNICAMENTE con un JSON válido que contenga:
    - 'is_correct' (true/false)
    - 'reason' (breve explicación)

    Pregunta: {question}
    Respuesta: {answer}
    """
    
    try:
        model_response = gemini_model.generate_content(prompt)
        evaluation = model_response.text.strip().lower()
        
        if evaluation == 'true':
            return True
        elif evaluation == 'false':
            return False
        else:
            # Si el modelo no devuelve lo esperado, fallamos seguros
            logging.warning(f"Respuesta inesperada del modelo: {evaluation}")
            return False
            
    except Exception as e:
        logging.error(f"Error al consultar el modelo: {str(e)}")
        return False
    
def extract_json_from_response(text: str) -> dict:
    """
    Extrae un JSON de la respuesta del modelo, incluso si contiene texto alrededor.
    """
    # Busca el primer bloque que parezca JSON
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if not json_match:
        raise ValueError("No se encontró JSON en la respuesta del modelo")
    
    try:
        return json.loads(json_match.group())
    except json.JSONDecodeError:
        raise ValueError("JSON inválido en la respuesta del modelo")
    
def is_correct(expected: str, response: str) -> bool:
    """Comparación difusa de respuestas con tolerancia a errores menores"""
    if not expected or not response:
        return False
    
    # Normalizar textos
    expected_norm = re.sub(r'\W+', ' ', expected.lower()).strip()
    response_norm = re.sub(r'\W+', ' ', response.lower()).strip()
    
    # Comparación exacta
    if expected_norm == response_norm:
        return True
    
    # Comparación difusa
    ratio = SequenceMatcher(None, expected_norm, response_norm).ratio()
    return ratio > 0.7

def estimate_N_per_stage(stage: int) -> int:
    """Estima cuántas entradas procesar por etapa según tokens disponibles"""
    tokens_per_entry = {
        1: 150,  # 2 campos
        2: 200,  # 3 campos
        3: 300,  # 5 campos
        4: 500,  # 9 campos
        5: 300,  # 5 campos
        6: 500   # 9 campos
    }[stage]
    
    available = min(
        TOKEN_BUDGET // tokens_per_entry,
        DAILY_LIMIT - requests_today,
        RPM_LIMIT - requests_this_minute
    )
    return max(5, min(20, available))  # Entre 5 y 20 por lote

# === EJECUCIÓN DE ETAPAS CORREGIDA ===
def run_stage(stage: int, round_num: int) -> bool:
    print(f"\n🚀 Iniciando Etapa {stage} (Vuelta {round_num})")
    logging.info(f"Iniciando Etapa {stage} (Vuelta {round_num})")
    
    N = estimate_N_per_stage(stage)
    print(f"📊 Estimado: {N} entradas para esta etapa")
    
    # Cargar datos
    files = list(DATA_DIR.glob("*.json"))
    if not files:
        print("⚠️ No se encontraron archivos JSON")
        return True
    
    selected_files = random.sample(files, min(N, len(files)))
    json_data = []
    for f in selected_files:
        try:
            with open(f, encoding="utf-8") as file:
                data = CocktailData(**json.load(file))
                json_data.append(data)
        except Exception as e:
            print(f"⚠️ Error en {f.name}: {str(e)}")
            logging.error(f"Error cargando {f.name}: {str(e)}")
    
    if not json_data:
        print("⚠️ No hay datos válidos para esta etapa")
        return True
    
    batch = []
    base_indices_config = {
        1: [0],  # 1 base de 2 campos
        2: [0],  # 1 base de 3 campos
        3: [0, 1],  # 2 bases de 5 campos
        4: [0, 1, 2],  # 3 bases de 9 campos
        5: [0],  # 1 base de 5 campos
        6: [0]   # 1 base de 9 campos
    }
    
    for data in json_data:
        fields = select_fields_for_stage(data, stage)
        if not fields:
            continue
        
        # Seleccionar índices base
        base_indices = base_indices_config[stage]
        if stage in [1, 2, 5, 6]:
            # Para estas etapas, seleccionar un índice base aleatorio
            base_indices = [random.randint(0, len(fields)-1)]
        elif stage == 3:
            # Seleccionar 2 índices base aleatorios
            base_indices = random.sample(range(len(fields)), 2)
        elif stage == 4:
            # Seleccionar 3 índices base aleatorios
            base_indices = random.sample(range(len(fields)), 3)
        
        batch.append((fields, base_indices))
    
    if not batch:
        print("⚠️ No se pudo preparar lote para esta etapa")
        return True
    
    try:
        prompt = build_prompt_adaptive(stage, batch)
        response_text = call_model(prompt)
        
        if response_text is None:
            print("⛔ Error crítico en llamada al modelo")
            return False
            
        questions = extract_questions(response_text)
        print(f"🔍 Extraídas {len(questions)} preguntas de la respuesta")
    except Exception as e:
        print(f"⛔ Error en el modelo: {str(e)}")
        logging.error(f"Error en modelo: {str(e)}")
        return True
    
    stats = {"OK": 0, "ERROR": 0}
    details = []
    
    for i, (fields, base_indices) in enumerate(batch):
        if i >= len(questions):
            print(f"⚠️ Faltan preguntas para la entrada {i+1}")
            continue
            
        q = questions[i]
        # Construir respuesta esperada con los campos objetivo
        expected_parts = []
        for idx, (name, value) in enumerate(fields):
            if idx not in base_indices:
                expected_parts.append(value)
        expected = ". ".join(expected_parts)
        
        if not expected:
            print(f"⚠️ Respuesta esperada vacía para entrada {i+1}")
            continue
            
        response = get_response(q)
        
        if get_true_correct(q, response):
            stats["OK"] += 1
            result_flag = "✅"
        else:
            stats["ERROR"] += 1
            result_flag = "❌"
        
        print(f"{result_flag} Q: {q[:70]}{'...' if len(q) > 70 else ''}")
        details.append({
            "stage": stage,
            "round": round_num,
            "question": q,
            "response": response,
            "expected": expected,
            "result": result_flag
        })
    
    # Guardar estadísticas
    try:
        with open(STATS_FILE, "r+", encoding="utf-8") as f:
            stats_data = json.load(f)
            stage_key = f"stage_{stage}"
            
            if stage_key not in stats_data:
                stats_data[stage_key] = {}
                
            round_key = f"round_{round_num}"
            if round_key not in stats_data[stage_key]:
                stats_data[stage_key][round_key] = stats
            else:
                # Actualizar estadísticas existentes
                existing = stats_data[stage_key][round_key]
                existing["OK"] += stats["OK"]
                existing["ERROR"] += stats["ERROR"]
            
            f.seek(0)
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
            f.truncate()
    except Exception as e:
        print(f"⛔ Error guardando estadísticas: {str(e)}")
        logging.error(f"Error guardando estadísticas: {str(e)}")
    
    # Guardar detalles
    try:
        with open(DETAIL_FILE, "r+", encoding="utf-8") as f:
            details_data = json.load(f)
            details_data.extend(details)
            f.seek(0)
            json.dump(details_data, f, ensure_ascii=False, indent=2)
            f.truncate()
    except Exception as e:
        print(f"⛔ Error guardando detalles: {str(e)}")
        logging.error(f"Error guardando detalles: {str(e)}")
    
    print(f"📊 Etapa {stage} completada: OK={stats['OK']}, ERROR={stats['ERROR']}")
    logging.info(f"Etapa {stage} completada: OK={stats['OK']}, ERROR={stats['ERROR']}")
    return True

# === FUNCIÓN PRINCIPAL MEJORADA ===
def main():
    start_time = time.time()
    stage_cycle = [1, 2, 3, 4, 5, 6]  # Orden de etapas
    stage_index = 0
    round_counter = 1
    requests_per_stage = {stage: 0 for stage in stage_cycle}
    stage_rounds = {stage: 0 for stage in stage_cycle}
    
    print(f"⏱️ Iniciando ejecución por {MAX_RUN_TIME/60} minutos")
    logging.info(f"Inicio ejecución. Tiempo máximo: {MAX_RUN_TIME/60} minutos")
    
    while (time.time() - start_time) < MAX_RUN_TIME:
        current_stage = stage_cycle[stage_index]
        stage_rounds[current_stage] = stage_rounds.get(current_stage, 0) + 1
        current_round = stage_rounds[current_stage]
        
        print(f"\n🔁 Vuelta {round_counter} | Etapa {current_stage} | Petición {requests_per_stage.get(current_stage, 0)+1}/10")
        logging.info(f"Vuelta {round_counter} - Etapa {current_stage}")
        
        # Ejecutar etapa
        success = run_stage(current_stage, current_round)
        if not success:
            print("⚠️ Error crítico, deteniendo ejecución")
            logging.error("Error crítico, deteniendo ejecución")
            break
            
        requests_per_stage[current_stage] = requests_per_stage.get(current_stage, 0) + 1
        
        # Rotar etapa si se completaron 10 peticiones
        if requests_per_stage.get(current_stage, 0) >= 10:
            print(f"🎯 Completadas 10 peticiones para Etapa {current_stage}")
            requests_per_stage[current_stage] = 0
            stage_index = (stage_index + 1) % len(stage_cycle)
        
        round_counter += 1
        
        # Pausa breve entre iteraciones
        time.sleep(1)
    
    # Guardar estado final de peticiones
    with open(REQUEST_LOG, "w") as f:
        f.write(str(requests_today))
    
    elapsed = time.time() - start_time
    print(f"\n🏁 Ejecución completada en {elapsed/60:.1f} minutos")
    print(f"📊 Total peticiones: {requests_today}")
    print(f"🔑 API keys usadas: {current_api_key_index+1}/{len(ALL_API_KEYS)}")
    logging.info(f"Ejecución completada. Tiempo: {elapsed/60:.1f} min, Peticiones: {requests_today}, Keys usadas: {current_api_key_index+1}")

# === INICIALIZACIÓN ===
if __name__ == "__main__":
    # Configurar modelo Gemini
    genai.configure(api_key=API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    
    print(f"🔑 Usando API key {current_api_key_index+1}/{len(ALL_API_KEYS)}")
    print(f"⏱️ Tiempo máximo de ejecución: {MAX_RUN_TIME/60} minutos")
    print(f"🔁 Orden de etapas: [1, 2, 3, 4, 5, 6]")
    
    main()