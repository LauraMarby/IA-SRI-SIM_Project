import json
from pathlib import Path

DATA_DIR = Path("src/data")
INGREDIENT_VECTORS_FILE = Path("src/flavor_space/ingredient_flavor_vectors.json")
OUTPUT_FILE = Path("src/flavor_space/cocktail_flavor_vectors.json")

def catch_ingredients_vectors(ingredients: list[str]) -> list[list[int]]:
    """
    Busca los vectores de sabores de los ingredientes de la receta.
    Args:
        ingredients(list[str]): Ingredientes del coctel.
    Returns:
        list[list[int]]: Vectores de sabores de los ingredientes del coctel.
    """
    
    vectors = []
    with open(INGREDIENT_VECTORS_FILE, "r", encoding="utf-8") as f:
        ingredient_vectors = json.load(f)

        for ingredient_key in ingredient_vectors:
            for ingredient in ingredients:
                if ingredient_key in ingredient.lower():
                    vectors.append(ingredient_vectors[ingredient_key])
                    break

    return vectors

def calculate_flavor_main(vectors: list[list[int]]) -> list[int]:
    """
    Calcula el nivel de pertenencia del coctel a cada sabor teniendo en cuenta el nivel de 
    pertenencia de sus ingredientes.
    Args:
        vectors(list[list[int]]): Nivel de pertenencia de los ingredientes del coctel.
    Result:
        list[int]: vector de pertenencia del coctel.
    """

    result = []
    for columna in zip(*vectors):
        sum = 0
        for value in columna:
            sum += value
        result.append(sum/len(columna))

    return result

def apply_fuzzy_logic_to_cocktails():
    """Verifica por cada coctel sus ingredientes y en dependencia del vector de sabores 
    de cada uno, guarda en un json los vectores de sabores de los cocteles."""
    
    data = {}
    for file in DATA_DIR.glob("*.json"):
        ingredients = []
        with open(file, "r", encoding="utf-8") as f:
            coctel = json.load(f)
            ingredients = coctel.get('Ingredients', [])
            vectors = catch_ingredients_vectors(ingredients)
            flavor_main = calculate_flavor_main(vectors)
            data[coctel['Name']] = flavor_main

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)

