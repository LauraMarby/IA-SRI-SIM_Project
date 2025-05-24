from agents.user_agent import UserAgent
from agents.coordinator_agent import CoordinatorAgent
from environment.environment import Environment
from agents.ontology_agent import OntologyAgent

if __name__ == "__main__":
    # user_agent = UserAgent()
    # coordinator = CoordinatorAgent()

    # user_input = user_agent.get_input()
    # coordinator.handle_query(user_input)

    env = Environment('src/ontology/ontology.owl')
    ontology_agent = OntologyAgent(env)
    env.register_agent('ontology', ontology_agent)

    print(ontology_agent.listar_tragos())  # Si hay datos, los mostrará