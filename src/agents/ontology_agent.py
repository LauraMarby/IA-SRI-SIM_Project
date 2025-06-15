import os
from owlready2 import get_ontology
from agents.base_agent import BaseAgent

class OntologyAgent(BaseAgent):
    def __init__(self, name, system, ontology_fn):
        super().__init__(name, system)
        self.ontology_fn = ontology_fn
        ONTOLOGY_PATH = os.path.abspath("src/ontology/ontology.owl")
        self.onto = get_ontology(f"file://{ONTOLOGY_PATH}").load()

    async def handle(self, message):
        cocktail = message["content"]["cocktails"]
        fields = message["content"]["fields"]
        print("[CONSULTANDO A LA ONTOLOGÍA]")
        results = self.ontology_fn(cocktail, fields, self.onto)
        filtered_results = []
        for result in results:
            if "Error" not in result:
                filtered_results.append(result)
        await self.send("validator", {"source": "ontology", "results": filtered_results, "type": "result"})