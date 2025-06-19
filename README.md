# Bartender Multiagent System 🍸

Este es un sistema multiagente con enfoque RAG para asistencia inteligente en la preparación y recomendación de cócteles.

### Desarrolladores: 
- Adrián Hernández Castellanos - C312
- Laura Martir Beltrán - C311
- Yesenia Valdés Rodríguez - C311

### Objetivo:
El objetivo es simular un asistente conversacional experto en coctelería, que no solo responda a preguntas frecuentes, sino que también adapte sus respuestas en función de la disponibilidad de datos, recurriendo a una estrategia
de recuperación de conocimiento cuando su conocimiento base no es suficiente.

### Requerimientos:
- Python 3.10+
- google generative AI API key
- beautifulsoup4
- google
- langdetect
- matplotlib
- nltk
- numpy
- owlready2
- requests
- sentence-transformers
- spacy
- sympy
- tenacity
- trafilatura
- urllib3
- google-generativeai

Nota: Es posible que sea necesaria una VPN. Los desarrolladores usan Windscribe para la ejecución de este programa.

## Componentes del sistema

- Agente usuario: inicia peticiones
- Agente coordinador: dirige las tareas
- Agente de conocimiento: accede a ontología
- Agente RAG: busca y genera respuestas usando un modelo de lenguaje
- Agente crawler: obtiene información actualizada
- Agente metaheurístico: optimiza combinaciones de cócteles
