from owlready2 import *
import os

ontology_path = os.path.abspath("src/ontology/ontology.owl")
onto = get_ontology(f"file://{ontology_path}").load()

with onto:
    class Cocktail(Thing): pass
    class Ingredient(Thing): pass

    def add_cocktail(name, ingredients):
        c = Cocktail(name.replace(" ", "_"))
        c.hasIngredient = [Ingredient(i.replace(" ", "_")) for i in ingredients]

    cocktails = [
        ("Mojito", ["Rum", "Mint", "Sugar"]),
        ("Margarita", ["Tequila", "Triple Sec", "Lime Juice"]),
        ("Old Fashioned", ["Bourbon", "Angostura Bitters", "Sugar"]),
        ("Caipirinha", ["Cachaça", "Lime", "Sugar"]),
        ("Daiquiri", ["Rum", "Lime Juice", "Sugar"]),
        ("Negroni", ["Gin", "Campari", "Vermouth"]),
        ("Cosmopolitan", ["Vodka", "Triple Sec", "Cranberry Juice"]),
        ("Mai Tai", ["Rum", "Lime Juice", "Orgeat Syrup"]),
        ("Piña Colada", ["Rum", "Pineapple Juice", "Coconut Cream"]),
        ("Manhattan", ["Whiskey", "Vermouth", "Angostura Bitters"]),
        ("Whiskey Sour", ["Whiskey", "Lemon Juice", "Sugar"]),
        ("Bloody Mary", ["Vodka", "Tomato Juice", "Tabasco"]),
        ("Gin Tonic", ["Gin", "Tonic Water"]),
        ("Tequila Sunrise", ["Tequila", "Orange Juice", "Grenadine"]),
        ("Cuba Libre", ["Rum", "Cola", "Lime"]),
        ("Tom Collins", ["Gin", "Lemon Juice", "Soda Water"]),
        ("Aperol Spritz", ["Aperol", "Prosecco", "Soda Water"]),
        ("Espresso Martini", ["Vodka", "Espresso", "Coffee Liqueur"]),
        ("Mint Julep", ["Bourbon", "Mint", "Sugar"]),
        ("French 75", ["Gin", "Champagne", "Lemon Juice"])
    ]

    for name, ingredients in cocktails:
        add_cocktail(name, ingredients)

# Guardar ontología actualizada
onto.save(file=ontology_path, format="rdfxml")
print("20 cócteles añadidos a la ontología.")
