import os
from owlready2 import get_ontology

# Ruta a la ontología
ONTOLOGY_PATH = os.path.abspath("src/ontology/ontology.owl")

# Cargar la ontología
onto = get_ontology(f"file://{ONTOLOGY_PATH}").load()

def consultar_tragos_ontologia(nombres_tragos, campos):
    resultados = []

    for nombre in nombres_tragos:
        resultado = {"Nombre": nombre}
        
        # Acceso por ID directamente
        cocktail = getattr(onto, nombre, None)

        if not cocktail:
            resultado["Error"] = f"Cóctel '{nombre}' no encontrado en la ontología."
            resultados.append(resultado)
            continue

        if campos[0]:  # Url
            resultado["Url"] = cocktail.hasUrl[0] if cocktail.hasUrl else ""

        if campos[1]:  # Vaso
            resultado["Glass"] = cocktail.servedIn[0].name.replace("_", " ") if cocktail.servedIn else ""

        if campos[2]:  # Ingredientes
            resultado["Ingredients"] = [i.name.replace("_", " ") for i in cocktail.hasIngredient] if cocktail.hasIngredient else []

        if campos[3]:  # Instrucciones
            resultado["Instructions"] = cocktail.hasInstructions[0].split(". ") if cocktail.hasInstructions else []

        if campos[4]:  # Review
            resultado["Review"] = cocktail.hasReview[0] if cocktail.hasReview else ""

        if campos[5]:  # Historia
            resultado["History"] = cocktail.hasHistory[0] if cocktail.hasHistory else ""

        if campos[6]:  # Nutrición
            resultado["Nutrition"] = cocktail.hasNutrition[0] if cocktail.hasNutrition else ""

        if campos[7]:  # Alcohol_Content
            if cocktail.hasAlcoholContent:
                ac = cocktail.hasAlcoholContent[0]
                resultado["Alcohol_Content"] = [
                    [ac.standardDrinks[0] if ac.standardDrinks else ""],
                    [ac.alcoholVolume[0] if ac.alcoholVolume else ""],
                    [ac.pureAlcohol[0] if ac.pureAlcohol else ""]
                ]
            else:
                resultado["Alcohol_Content"] = []

        if campos[8]:  # Garnish
            resultado["Garnish"] = cocktail.hasGarnish[0] if cocktail.hasGarnish else ""

        resultados.append(resultado)

    return resultados


