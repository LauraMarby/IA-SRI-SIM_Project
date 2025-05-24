from agents.user_agent import UserAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.ontology_agent import OntologyAgent
from environment.environment import Environment

if __name__ == "__main__":
    env = Environment('src/ontology/ontology.owl')
    ontology_agent = OntologyAgent(env)
    env.register_agent('ontology', ontology_agent)

    coordinator = CoordinatorAgent(env)
    env.register_agent('coordinator', coordinator)

    user_agent = UserAgent(env)
    user_agent.interact()

