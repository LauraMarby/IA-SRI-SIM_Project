from src.agents.intent_detector_agent import detectar_intencion

mensajes = [
    "¿Qué tragos tienes?",
    "¿Qué lleva el Negroni?",
    "¿Qué me recomiendas con whisky?",
    "¿De dónde es el Margarita?",
    "¿Cómo se prepara un Daiquiri?",
    "¿Este trago es de color azul?"
]

for msg in mensajes:
    print(f"\"{msg}\" → {detectar_intencion(msg)}")
