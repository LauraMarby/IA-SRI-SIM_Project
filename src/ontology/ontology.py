from owlready2 import *

# Crear una nueva ontología
onto = get_ontology("http://www.bartender-project.org/ontology#")

with onto:
    # Clases
    class Cocktail(Thing): pass
    class Ingredient(Thing): pass
    class Glass(Thing): pass
    class Preparation(Thing): pass
    class Country(Thing): pass
    class Category(Thing): pass
    class Rating(Thing): pass
    class Person(Thing): pass
    class PriceRange(Thing): pass

    # Propiedades entre objetos (relaciones)
    class hasIngredient(Cocktail >> Ingredient): pass
    class servedIn(Cocktail >> Glass): pass
    class hasPreparation(Cocktail >> Preparation): pass
    class originCountry(Cocktail >> Country): pass
    class belongsToCategory(Cocktail >> Category): pass
    class createdBy(Cocktail >> Person): pass

    # Propiedades de datos (atributos)
    class hasHistory(Cocktail >> str, DataProperty): pass
    class hasRating(Cocktail >> float, DataProperty): pass
    class hasPrice(Cocktail >> str, DataProperty): pass

# Guardar ontología
onto.save(file = "src/ontology/ontology.owl", format = "rdfxml")
print("Ontología guardada como bartender.owl")
