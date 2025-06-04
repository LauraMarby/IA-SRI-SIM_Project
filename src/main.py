import os
import asyncio
import google.generativeai as genai
from environment.agent_system import AgentSystem
from agents.user_agent import UserAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.ontology_agent import OntologyAgent
from agents.embedding_agent import EmbeddingAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.intent_detector_agent import IntentDetectorAgent
from ontology.query_ontology import consultar_tragos
from embedding.query_embedding import retrieve

async def main():

    genai.configure(api_key="AIzaSyDeWmnKHVRu-QVPPxKpU7EjT6rmrAWtvbY")
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")

    system = AgentSystem()

    user = UserAgent("user", system)
    coordinator = CoordinatorAgent("coordinator", system)
    ontology = OntologyAgent("ontology", system, consultar_tragos)
    embedding = EmbeddingAgent("embedding", system, retrieve)
    knowledge = KnowledgeAgent("knowledge", system)
    intent_detector = IntentDetectorAgent("intent_detector", system, gemini_model)

    for agent in [coordinator, ontology, knowledge, user, intent_detector, embedding]:
        system.register_agent(agent)

    await asyncio.gather(
        user.run(),
        coordinator.run(),
        ontology.run(),
        embedding.run(),
        knowledge.run(),
        intent_detector.run()
    )

if __name__ == "__main__":
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(ROOT_DIR)
    asyncio.run(main())
