from owlready2 import *

class OntologyAgent:
    def __init__(self, env):
        self.onto = env.ontology

    def listar_tragos(self):
        return [cocktail.name for cocktail in self.onto.Cocktail.instances()]

    def ingredientes_de(self, nombre):
        for c in self.onto.Cocktail.instances():
            if c.name.lower() == nombre.lower():
                return [ing.name for ing in c.hasIngredient]
        return []


# Prueba
if __name__ == "__main__":
    agente = OntologyAgent("src/ontology/bartender.owl")
    print("Cócteles:", agente.listar_tragos())
    print("Ingredientes de Mojito:", agente.ingredientes_de("Mojito"))
