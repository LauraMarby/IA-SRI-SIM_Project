import os
import sys
from agents.user_agent import UserAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.ontology_agent import OntologyAgent
from environment.environment import Environment
from embedding.embedder import create_vectorstore, load_vectorstore, VECTORSTORE_PATH

if __name__ == "__main__":

    # Estableciendo ruta raíz del proyecto
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(ROOT_DIR)

    env = Environment('src/ontology/ontology.owl')
    ontology_agent = OntologyAgent(env)
    env.register_agent('ontology', ontology_agent)

    coordinator = CoordinatorAgent(env)
    env.register_agent('coordinator', coordinator)

    user_agent = UserAgent(env)
    user_agent.interact()

