import json
from pathlib import Path

DATA_DIR = Path("src/data")
OUTPUT_FILE = Path("src/flavor_space/ingredients_flavor.json")

def extract_all_ingredients():
    """Extrae todos los ingredientes en un .json con repetición"""
    all_ingredients = []

    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_ingredients.extend(data.get('Ingredients', []))
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as jsonfile:
        json.dump(all_ingredients, jsonfile, indent=2, ensure_ascii=False)
