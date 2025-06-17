import os
import asyncio
import google.generativeai as genai
from environment.agent_system import AgentSystem
from agents.user_agent import UserAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.ontology_agent import OntologyAgent
from agents.embedding_agent import EmbeddingAgent
from agents.crawler_agent import Crawler_Agent
from agents.intent_detector_agent import IntentDetectorAgent
from agents.validator_agent import ValidationAgent
from agents.flavor_agent import Flavor_Agent
from ontology.query_ontology import consultar_tragos
from embedding.query_embedding import retrieve
from pathlib import Path

"""
Script principal para inicializar y ejecutar el sistema multiagente de bartender.

Este script realiza las siguientes tareas:
- Carga el token de API desde un archivo local para autenticar la API de Google Generative AI.
- Configura el modelo generativo Gemini 1.5 de Google.
- Crea una instancia del sistema de agentes (`AgentSystem`).
- Inicializa los agentes necesarios, cada uno con sus responsabilidades específicas:
  * `UserAgent`: Agente que representa al usuario.
  * `CoordinatorAgent`: Coordinador que gestiona la interacción entre agentes.
  * `OntologyAgent`: Agente encargado de consultas a la ontología de cócteles.
  * `EmbeddingAgent`: Agente que gestiona búsquedas vectoriales.
  * `IntentDetectorAgent`: Agente que detecta intenciones del usuario usando el modelo.
  * `ValidationAgent`: Agente que valida respuestas usando el modelo.
  * `Crawler_Agent`: Agente que realiza scraping o crawling.
  * `Flavor_Agent`: Agente especializado en sabores y consultas extendidas.
- Registra los agentes en el sistema.
- Ejecuta todos los agentes concurrentemente con `asyncio.gather`.
- Cambia el directorio de trabajo al directorio raíz del proyecto para asegurar rutas relativas correctas.

Funciones clave:
- `load_token(file_path)`: Lee el token de API desde un archivo, manejando errores comunes.

Uso:
Ejecutar este archivo iniciará el sistema multiagente en modo asíncrono, permitiendo que
los agentes trabajen en paralelo para atender consultas y coordinar respuestas.

Requisitos:
- Archivo `src/token.txt` con el token válido para la API de Google Generative AI.
- Dependencias adecuadas instaladas (asyncio, google.generativeai, etc.).

Ejemplo de ejecución:
    python src/main.py
"""

def load_token(file_path="src/token.txt") -> str:
    try:
        token = Path(file_path).read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError("El archivo está vacío.")
        return token
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ No se encontró el archivo '{file_path}'")
    except Exception as e:
        raise RuntimeError(f"❌ Error al leer el token: {e}")

async def main():

    TOKEN = load_token()

    if TOKEN is None:
        raise ValueError("❌ No se encontró el token. ¿Está definido en config.env?")
    
    print(f"🔐 Token cargado: {TOKEN[:5]}...")  # Nunca muestres el token completo

    genai.configure(api_key=TOKEN)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")

    system = AgentSystem()

    user = UserAgent("user", system)
    coordinator = CoordinatorAgent("coordinator", system, gemini_model)
    ontology = OntologyAgent("ontology", system, consultar_tragos)
    embedding = EmbeddingAgent("embedding", system, retrieve)
    intent_detector = IntentDetectorAgent("intent_detector", system, gemini_model)
    validator = ValidationAgent("validator", system, gemini_model)
    crawler = Crawler_Agent("crawler", system)
    flavor = Flavor_Agent("flavor", system, consultar_tragos)

    for agent in [coordinator, ontology, user, intent_detector, embedding, validator, crawler, flavor]:
        system.register_agent(agent)

    await asyncio.gather(
        user.run(),
        coordinator.run(),
        ontology.run(),
        embedding.run(),
        intent_detector.run(),
        validator.run(),
        crawler.run(),
        flavor.run()
    )

if __name__ == "__main__":
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(ROOT_DIR)
    asyncio.run(main())
