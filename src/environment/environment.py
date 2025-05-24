from owlready2 import *

class Environment:
    def __init__(self, ontology_path):
        self.ontology = get_ontology(f"file://{ontology_path}").load()
        self.agents = {}

    def register_agent(self, name, agent):
        self.agents[name] = agent

    def get_agent(self, name):
        return self.agents.get(name)
