from owlready2 import *

onto = get_ontology("http://www.bartender-project.org/ontology#")

with onto:
    # Clases
    class Cocktail(Thing): pass
    class Ingredient(Thing): pass
    class Glass(Thing): pass
    class AlcoholContent(Thing): pass

    # Propiedades entre objetos
    class hasIngredient(Cocktail >> Ingredient): pass
    class servedIn(Cocktail >> Glass): pass
    class hasAlcoholContent(Cocktail >> AlcoholContent): pass

    # Propiedades de datos
    class hasName(Cocktail >> str, DataProperty): pass
    class hasUrl(Cocktail >> str, DataProperty): pass
    class hasInstructions(Cocktail >> str, DataProperty): pass
    class hasReview(Cocktail >> str, DataProperty): pass
    class hasHistory(Cocktail >> str, DataProperty): pass
    class hasNutrition(Cocktail >> str, DataProperty): pass
    class hasGarnish(Cocktail >> str, DataProperty): pass

    # Atributos para AlcoholContent
    class standardDrinks(AlcoholContent >> str, DataProperty): pass
    class alcoholVolume(AlcoholContent >> str, DataProperty): pass
    class pureAlcohol(AlcoholContent >> str, DataProperty): pass

# Guardar ontología
onto.save(file="src/ontology/ontology.owl", format="rdfxml")
print("Ontología actualizada guardada en src/ontology/ontology.owl")
