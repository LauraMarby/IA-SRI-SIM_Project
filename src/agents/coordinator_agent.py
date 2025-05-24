from agents.intent_detector_agent import detectar_intencion

class CoordinatorAgent:
    def __init__(self, env):
        self.env = env

    def handle_query(self, user_input):
        print(f"[Coordinador] Recibida la consulta: {user_input}")

        intencion = detectar_intencion(user_input)
        print(f"[Coordinador] Intención detectada: {intencion}")

        ontology_agent = self.env.get_agent('ontology')

        if intencion == "listar_cocteles":
            resultados = ontology_agent.listar_tragos()
            print("Tragos disponibles:")
            for r in resultados:
                print(f" - {r}")

        elif intencion == "ingredientes_de":
            nombre = self._extraer_nombre_coctel(user_input)
            ingredientes = ontology_agent.ingredientes_de(nombre)
            print(f"Ingredientes de {nombre}:")
            for ing in ingredientes:
                print(f" - {ing}")

        elif intencion == "preparacion_de":
            nombre = self._extraer_nombre_coctel(user_input)
            preparacion = ontology_agent.preparacion_de(nombre)
            print(f"Preparación de {nombre}:\n{preparacion}")

        elif intencion == "origen_cocktail":
            nombre = self._extraer_nombre_coctel(user_input)
            origen = ontology_agent.origen_de(nombre)
            print(f"Origen de {nombre}: {origen}")

        elif intencion == "recomendar_por_ingrediente":
            ingrediente = self._extraer_nombre_ingrediente(user_input)
            recomendados = ontology_agent.recomendar_por_ingrediente(ingrediente)
            print(f"Cócteles con {ingrediente}:")
            for r in recomendados:
                print(f" - {r}")

        else:
            print("[Coordinador] Intención no soportada o no reconocida.")

    def _extraer_nombre_coctel(self, texto):
        # TODO: Usar NER en producción. Aquí un parche simple:
        palabras = texto.split()
        for i, p in enumerate(palabras):
            if p.lower() in ["del", "de", "del", "el", "la"] and i+1 < len(palabras):
                return ' '.join(palabras[i+1:])
        return palabras[-1]  # Última palabra como fallback

    def _extraer_nombre_ingrediente(self, texto):
        # TODO: Mejorar con NLP si es necesario
        palabras = texto.split()
        if "con" in palabras:
            idx = palabras.index("con")
            return palabras[idx + 1] if idx + 1 < len(palabras) else ""
        return palabras[-1]
