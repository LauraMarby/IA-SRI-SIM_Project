from agents.intent_detector_agent import detect_intent

mensajes = [
    "¿Qué tragos tienes?",
    "Cómo se hace un mojito",
    "¿Qué lleva el Negroni?",
    "Dame la historia y los ingredientes del margarita",
    "Recomiéndame un trago dulce y un poco ácido",
    "Busca en internet los últimos cócteles de moda",
    "Qué cóctel lleva limón y menta pero no lleva alcohol",
]

parametros_explicitos = [

]

for msg in mensajes:
    print(f"\"{msg}\" → {detect_intent(msg)}")
