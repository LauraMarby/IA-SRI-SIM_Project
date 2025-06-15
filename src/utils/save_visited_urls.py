import json
from pathlib import Path


DATA_DIR = Path("src/data")
OUTPUT_FILE = Path("src/visited_urls.txt")

def save_data_visited_urls():
    """Guardar las urls que están predefinidas en la base de datos."""
    visited_urls = []

    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            visited_urls.append(data.get('Url'))
    
    contenido = ",".join(visited_urls)

    with open(OUTPUT_FILE, "w") as f:
        f.write(contenido)

def save_url_visited_urls(url: str):
    """Añadir url nueva a la lista de urls visitadas."""
    with open(OUTPUT_FILE, "r") as f:
        data = f.read().strip()  

    with open(OUTPUT_FILE, "a") as f:
        if data:  
            f.write(",")  
        f.write(url) 

def is_url_visited(url: str):
    """Verificar si la url ha sido visitada."""
    with open(OUTPUT_FILE, "r") as f:
        data = f.read()
        urls = data.split(",")  
        return url in urls