from owlready2 import *
import os

ontology_path = os.path.abspath("../ontology/ontology.owl")
onto = get_ontology(f"file://{ontology_path}").load()

with onto:
    # Crear instancias
    class Cocktail(Thing): pass
    class Ingredient(Thing): pass

    mojito = Cocktail("Mojito")
    rum = Ingredient("Rum")
    mint = Ingredient("Mint")

    mojito.hasIngredient = [rum, mint]

# Guardar ontología actualizada
onto.save(file=ontology_path, format="rdfxml")
print("Instancias añadidas y ontología guardada.")
