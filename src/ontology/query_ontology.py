from utils.text_preprocessing import normalize

def consultar_tragos(nombres_tragos, campos, onto):
    """
    Consulta información detallada de una lista de cócteles en una ontología.

    Para cada cóctel dado en `nombres_tragos`, obtiene los campos solicitados
    según la lista booleana correspondiente en `campos`. Los datos se extraen
    de la ontología `onto`.

    Parámetros:
        nombres_tragos (list of str): Lista con los nombres de los cócteles a consultar.
        campos (list of list of bool): Lista de listas booleanas que indican qué campos
            se deben extraer para cada cóctel. La estructura por cada lista es:
            [Url, Vaso, Ingredientes, Instrucciones, Review, Historia, Nutrición, Alcohol_Content, Garnish]
            Cada posición con valor True indica que se debe extraer ese campo.
        onto (objeto ontología): Instancia de la ontología donde se encuentran los cócteles
            y sus propiedades.

    Retorna:
        list of dict: Lista de diccionarios con la información consultada para cada cóctel.
            Cada diccionario contiene al menos la clave "Nombre" con el nombre del cóctel.
            Si el cóctel no existe en la ontología, incluye la clave "Error" con un mensaje.
            Para los campos solicitados, se incluyen las claves correspondientes con sus valores.
            En caso de que alguna propiedad no esté presente, se devuelve cadena vacía o estructura vacía.
    """

    resultados = []

    for nombre, campos_trago in zip(nombres_tragos, campos):
        resultado = {"Nombre": nombre}
        nombre_normalizado = normalize(nombre)
        cocktail = getattr(onto, nombre_normalizado, None)

        if not cocktail:
            resultado["Error"] = f"Cóctel '{nombre}' no encontrado en la ontología."
            resultados.append(resultado)
            continue

        if campos_trago[0]:  # Url
            resultado["Url"] = cocktail.hasUrl[0] if cocktail.hasUrl else ""

        if campos_trago[1]:  # Vaso
            resultado["Glass"] = cocktail.servedIn[0].name.replace("_", " ") if cocktail.servedIn else ""

        if campos_trago[2]:  # Ingredientes
            resultado["Ingredients"] = [i.name.replace("_", " ") for i in cocktail.hasIngredient] if cocktail.hasIngredient else []

        if campos_trago[3]:  # Instrucciones
            resultado["Instructions"] = cocktail.hasInstructions[0] if cocktail.hasInstructions else ""

        if campos_trago[4]:  # Review
            resultado["Review"] = cocktail.hasReview[0] if cocktail.hasReview else ""

        if campos_trago[5]:  # Historia
            resultado["History"] = cocktail.hasHistory[0] if cocktail.hasHistory else ""

        if campos_trago[6]:  # Nutrición
            resultado["Nutrition"] = cocktail.hasNutrition[0] if cocktail.hasNutrition else ""

        if campos_trago[7]:  # Alcohol_Content
            if cocktail.hasAlcoholContent:
                ac = cocktail.hasAlcoholContent[0]
                resultado["Alcohol_Content"] = {
                    "Standard Drinks": ac.standardDrinks[0] if ac.standardDrinks else "",
                    "Alcohol Volume": ac.alcoholVolume[0] if ac.alcoholVolume else "",
                    "Pure Alcohol": ac.pureAlcohol[0] if ac.pureAlcohol else ""
                }
            else:
                resultado["Alcohol_Content"] = {}

        if campos_trago[8]:  # Garnish
            resultado["Garnish"] = cocktail.hasGarnish[0] if cocktail.hasGarnish else ""

        resultados.append(resultado)

    return resultados
