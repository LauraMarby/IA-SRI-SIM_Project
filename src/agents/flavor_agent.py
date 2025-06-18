import json
from sympy import to_dnf, And, Or
from agents.base_agent import BaseAgent
import os
from owlready2 import get_ontology
from agents.base_agent import BaseAgent
from utils.softmax import softmax, select_k_without_replace


class Flavor_Agent(BaseAgent):
    """
    Agente especializado en descripciones de sabor, recomendaciones sensoriales y preferencias.

    Este agente interpreta preferencias del usuario (por ejemplo, "quiero algo dulce y suave"),
    filtra las bebidas disponibles según perfiles de sabor, y colabora con el CoordinatorAgent
    para enriquecer las recomendaciones personalizadas.

    Responsabilidades:
    - Interpretar preferencias sensoriales.
    - Asociar descriptores de sabor a bebidas.
    - Retornar tragos alineados con gustos específicos.

    """

    def __init__(self, name, system, ontology_fn):
        """
        Inicializa el agente de sabores.

        Este agente permite hacer consultas basadas en perfiles de sabor de los cócteles.
        Utiliza un archivo JSON que contiene vectores de sabores, y aplica reglas lingüísticas
        sobre ellos (como "muy dulce", "poco ácido", etc.) para filtrar recomendaciones.
        Finalmente, consulta la ontología para enriquecer las respuestas.

        Args:
            name (str): Nombre del agente.
            system (System): Referencia al sistema multiagente.
            ontology_fn (Callable): Función de consulta a la ontología, para expandir o filtrar resultados.
        """

        super().__init__(name, system)
        self.ontology_fn = ontology_fn
        ONTOLOGY_PATH = os.path.abspath("src/ontology/ontology.owl")
        self.onto = get_ontology(f"file://{ONTOLOGY_PATH}").load()

        self.categories = {
            "nada": lambda x: 1.0 if x <= 0.1 else 0.0,
            "poco": lambda x: max(min((x - 0.1)/0.15, (0.4 - x)/0.15), 0.0),  
            "medio": lambda x: max(min((x - 0.3)/0.2, (0.7 - x)/0.2), 0.0),  
            "muy": lambda x: 1.0 if x >= 0.8 else max(0.0, (x - 0.6)/0.2)
        }
        self.flavor_map = {
            "dulce": 0,
            "salado": 1,
            "amargo": 2,
            "ácido": 3,
            "picante": 4
        }
        
        self.DATA_FILE = "src/flavor_space/cocktail_flavor_vectors.json"

        with open(self.DATA_FILE, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def query_to_dnf(self, query):
        """
        Convierte una fórmula lógica textual a su Forma Normal Disyuntiva (DNF).

        Args:
            query (str): Expresión booleana en lenguaje natural con conectores AND, OR y modificadores de sabor.

        Returns:
            sympy.Expr: Fórmula equivalente en DNF.
        """

        treated = query.lower().replace('and', '&').replace('or', '|').replace('not', '~')
        dnf = to_dnf(treated, simplify=True)
        return dnf
    
    def get_clauses(self, expr):
        """
        Obtiene las cláusulas de una expresión booleana en forma DNF.

        Args:
            expr (sympy.Expr): Fórmula DNF.

        Returns:
            tuple: Clausulas que componen la expresión (una o varias).
        """

        if isinstance(expr, Or):
            return expr.args
        else:
            return (expr,)
        
    def get_terms(self, clause):
        """
        Obtiene los términos individuales dentro de una cláusula booleana.

        Args:
            clause (sympy.Expr): Una cláusula (AND o literal).

        Returns:
            tuple: Lista de términos.
        """

        if isinstance(clause, And):
            return clause.args
        else:
            return (clause,)
        
    def evaluate_term(self, term, cocktail_vector):
        """
        Evalúa un término lingüístico (ej. 'muy_dulce') sobre el vector de sabores de un cóctel.

        Args:
            term (sympy.Symbol): Término a evaluar.
            cocktail_vector (list[float]): Vector de sabores del cóctel.

        Returns:
            float: Valor de pertenencia en el rango [0.0, 1.0].
        """

        term_str = str(term)
        
        parts = term_str.split('_')
        
        if len(parts) == 2:
            modifier, flavor = parts
        else:
            modifier, flavor = "medio", parts[0]
        
        if flavor not in self.flavor_map:
            return 0.0  
        
        flavor_idx = self.flavor_map[flavor]
        flavor_value = cocktail_vector[flavor_idx]
        
        if modifier in self.categories:
            return self.categories[modifier](flavor_value)
        else:
            return 0.0
    
    def es_formula_valida(self, expresion: str) -> bool:
        """
        Verifica que la fórmula ingresada sea válida.

        Args:
            expresion (str): Fórmula ingresada por el usuario.

        Returns:
            bool: True si todos los términos y operadores son válidos, False en caso contrario.
        """

        permitidos = {
            "nada_dulce", "poco_dulce", "medio_dulce", "muy_dulce", "dulce"
            "nada_amargo", "poco_amargo", "medio_amargo", "muy_amargo", "amargo"
            "nada_salado", "poco_salado", "medio_salado", "muy_salado", "salado"
            "nada_ácido", "poco_ácido", "medio_ácido", "muy_ácido", "ácido"
            "nada_picante", "poco_picante", "medio_picante", "muy_picante", "picante"
            "AND", "OR"
        }

        tokens = expresion.strip().split()
        if not tokens:
            return False
        return all(token in permitidos for token in tokens)

    async def handle(self, message: str) -> list[(str, int)]:
        """
        Recomienda cócteles basados en una lista de fórmulas lógicas.

        Args:
            message: dict con keys:
                - content: dict con key 'flavors': list[str]
                - amount: int (cuántos tragos por fórmula)
        Returns:
            list[(str, int)]: Lista de tuplas (nombre, valor) ordenadas descendente
        """

        flavor_formulas = message["content"]["flavors"]
        amount = message["content"].get("ammount", 1)

        if not flavor_formulas or not isinstance(flavor_formulas, list):
            await self.send("validator", {"source": "flavor", "results": [], "type": "result"})
            return

        final_results = []

        for formula in flavor_formulas:
            if not self.es_formula_valida(formula):
                continue

            try:
                message_dnf = self.query_to_dnf(formula)
            except Exception as e:
                print(f"[Flavor_Agent] Error al convertir a DNF: {e}")
                continue

            scored_candidates = []

            for cocktail in self.data:
                cocktail_vector = self.data[cocktail]
                max_value = 0.0

                for clause in self.get_clauses(message_dnf):
                    min_value = 1.0
                    for term in self.get_terms(clause):
                        term_value = self.evaluate_term(term, cocktail_vector)
                        min_value = min(min_value, term_value)
                    max_value = max(max_value, min_value)

                if max_value >= 0.7:
                    scored_candidates.append((cocktail, max_value))

            if not scored_candidates:
                continue

            # Softmax y selección top-k para cada fórmula
            probs = softmax(scored_candidates)
            top_k = select_k_without_replace(probs, amount)

            for name, _ in top_k:
                final_results.append(name)

        if not final_results:
            await self.send("validator", {"source": "flavor", "results": [], "type": "result"})
            return

        # Generar campos dummy y consultar la ontología
        dummy_fields = [[True]*9 for _ in final_results]
        ontology_results = self.ontology_fn(final_results, dummy_fields, self.onto)

        filtered_results = [res for res in ontology_results if "Error" not in res]

        await self.send("validator", {"source": "flavor", "results": filtered_results, "type": "result"})
