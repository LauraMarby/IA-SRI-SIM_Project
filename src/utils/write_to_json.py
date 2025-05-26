import json
import os
import re

def slugify(name):
    """Convierte un nombre en un nombre de archivo amigable."""
    name = name.lower()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s]+', '_', name)
    return name

def write_to_json(data):
    """
    Write data to a json file

    Arg:
        - data (list<dict>) : List of dictionaries. It is assumed that each dictionary has the same keys.

    """

    output_folder = 'src/data'
    os.makedirs(output_folder, exist_ok=True)

    filename = slugify(data["Name"]) + '.json'
    filepath = os.path.join(output_folder, filename)

    with open(filepath, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)

    print(f'Guardado: {filepath}')
