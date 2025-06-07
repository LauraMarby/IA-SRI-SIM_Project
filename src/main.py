import os
import asyncio
import google.generativeai as genai
from environment.agent_system import AgentSystem
from agents.user_agent import UserAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.ontology_agent import OntologyAgent
from agents.embedding_agent import EmbeddingAgent
from agents.intent_detector_agent import IntentDetectorAgent
from agents.validator_agent import ValidationAgent
from ontology.query_ontology import consultar_tragos
from embedding.query_embedding import retrieve
from pathlib import Path

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
    coordinator = CoordinatorAgent("coordinator", system)
    ontology = OntologyAgent("ontology", system, consultar_tragos)
    embedding = EmbeddingAgent("embedding", system, retrieve)
    intent_detector = IntentDetectorAgent("intent_detector", system, gemini_model)
    validator = ValidationAgent("validator", system, gemini_model)

    for agent in [coordinator, ontology, user, intent_detector, embedding, validator]:
        system.register_agent(agent)

    await asyncio.gather(
        user.run(),
        coordinator.run(),
        ontology.run(),
        embedding.run(),
        intent_detector.run(),
        validator.run()
    )

if __name__ == "__main__":
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(ROOT_DIR)
    asyncio.run(main())
