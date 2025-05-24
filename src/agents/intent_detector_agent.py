import re

import re

INTENTS = {
    "saludo": [
        r"^\s*(hola|buenas|buenos días|buenas tardes|buenas noches|hey|qué tal)\b",
    ],
    "listar_cocteles": [
        r"(qué|cuales).*tragos|cocteles|bebidas.*(hay|tienes)",
        r"lista.*(tragos|cocteles|bebidas)"
    ],
    "ingredientes_de": [
        r"(qué|cuales).*ingredientes.*(lleva|tiene).*",
        r"(qué|cuales).*lleva el|la.*"
    ],
    "recomendar_por_ingrediente": [
        r"(qué|cual).*recomiendas.*",
        r"recomiéndame.*",
        r"una bebida.*(con|que tenga).*"
    ],
    "origen_cocktail": [
        r"(de dónde|cuál es el origen).*",
        r"(dónde).*se creó.*"
    ],
    "preparacion_de": [
        r"(cómo se hace|cómo preparar|preparación de|como se hace|como preparar|preparacion de).*",
        r"(cómo hago|como hago).*"
    ],
}

def detectar_intencion(mensaje: str) -> str:
    mensaje = mensaje.lower().strip()
    for intent, patrones in INTENTS.items():
        for patron in patrones:
            if re.search(patron, mensaje):
                return intent
    return "desconocida"
