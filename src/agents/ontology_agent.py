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

    def preparacion_de(self, nombre):
        for c in self.onto.Cocktail.instances():
            if c.name.lower() == nombre.lower():
                if hasattr(c, 'preparation'):
                    return c.preparation[0] if c.preparation else "No hay instrucciones disponibles."
                else:
                    return "Este cóctel no tiene información de preparación."
        return "Cóctel no encontrado."

    def origen_de(self, nombre):
        for c in self.onto.Cocktail.instances():
            if c.name.lower() == nombre.lower():
                if hasattr(c, 'origin'):
                    return c.origin[0] if c.origin else "Origen desconocido."
                else:
                    return "Este cóctel no tiene información de origen."
        return "Cóctel no encontrado."

    def recomendar_por_ingrediente(self, ingrediente_nombre):
        resultado = []
        for c in self.onto.Cocktail.instances():
            for ing in c.hasIngredient:
                if ing.name.lower() == ingrediente_nombre.lower():
                    resultado.append(c.name)
                    break
        return resultado
