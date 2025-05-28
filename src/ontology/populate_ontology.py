import os
import json
import unicodedata
from owlready2 import *\

# Rutas
ONTOLOGY_PATH = "src/ontology/ontology.owl"
DATA_DIR = "src/data"

# Cargar la ontología existente
onto = get_ontology(f"file://{os.path.abspath(ONTOLOGY_PATH)}").load()

# Helper: normalizar nombres para IDs y búsquedas
def normalize(name):
    # Quitar tildes, pasar a minúsculas, reemplazar espacios y otros caracteres
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("utf-8")
    return name.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "").replace("/", "_")

# Recorrer todos los archivos JSON
for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json"):
        path = os.path.join(DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"❌ Error cargando {filename}: {e}")
                continue

            try:
                # Crear instancia del cóctel
                cocktail_id = normalize(data["Name"])
                cocktail = onto.Cocktail(cocktail_id)
                cocktail.hasName = [data["Name"]]
                cocktail.hasUrl = [data["Url"]]
                cocktail.hasInstructions = [" ".join(data.get("Instructions", []))]
                cocktail.hasReview = [data.get("Review", "")]
                cocktail.hasHistory = [data.get("History", "")]
                cocktail.hasNutrition = [data.get("Nutrition", "")]
                cocktail.hasGarnish = [data.get("Garnish", "")]
                
                # Ingredientes
                for ing in data.get("Ingredients", []):
                    ing_id = normalize(ing)
                    ing_instance = onto.search_one(iri=f"{onto.base_iri}{ing_id}")
                    if not ing_instance:
                        ing_instance = onto.Ingredient(ing_id)
                    cocktail.hasIngredient.append(ing_instance)

                # Vaso
                glass = data.get("Glass")
                if glass:
                    glass_id = normalize(glass)
                    glass_instance = onto.search_one(iri=f"{onto.base_iri}{glass_id}")
                    if not glass_instance:
                        glass_instance = onto.Glass(glass_id)
                    cocktail.servedIn = [glass_instance]


                # Alcohol content
                ac_data = data.get("Alcohol_Content", [])
                if len(ac_data) == 3:
                    ac_id = f"{cocktail_id}_Alcohol"
                    ac = onto.AlcoholContent(ac_id)
                    ac.standardDrinks = [ac_data[0][0]]
                    ac.alcoholVolume = [ac_data[1][0]]
                    ac.pureAlcohol = [ac_data[2][0]]
                    cocktail.hasAlcoholContent = [ac]

                print(f"✅ Insertado: {data['Name']}")

            except Exception as e:
                print(f"❌ Error procesando {filename}: {e}")

# Guardar ontología actualizada
onto.save(file=ONTOLOGY_PATH, format="rdfxml")
print(f"📦 Ontología actualizada y guardada en {ONTOLOGY_PATH}")
