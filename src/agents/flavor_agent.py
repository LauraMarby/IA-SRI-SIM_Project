import json
from sympy import to_dnf, And, Or
from agents.base_agent import BaseAgent
import os
from owlready2 import get_ontology
from agents.base_agent import BaseAgent
from utils.softmax import softmax, select_k_without_replace


class Flavor_Agent(BaseAgent):
    def __init__(self, name, system, ontology_fn):
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
        Transforma una expresión booleana en su forma normal disyuntiva.
        """
        treated = query.lower().replace('and', '&').replace('or', '|').replace('not', '~')
        dnf = to_dnf(treated, simplify=True)
        return dnf
    
    def get_clauses(self, expr):
        """ Obtiene las clausuras de una expresión normal disyuntiva."""
        if isinstance(expr, Or):
            return expr.args
        else:
            return (expr,)
        
    def get_terms(self, clause):
        """ Obtiene los términos de una clausura."""
        if isinstance(clause, And):
            return clause.args
        else:
            return (clause,)
        
    def evaluate_term(self, term, cocktail_vector):
        """Evalúa un término lingüístico contra el vector del cóctel."""
        term_str = str(term)
        
        parts = term_str.split('_')
        
        if len(parts) == 2:
            modifier, flavor = parts
        else:
            modifier, flavor = "muy", parts[0]
        
        if flavor not in self.flavor_map:
            return 0.0  
        
        flavor_idx = self.flavor_map[flavor]
        flavor_value = cocktail_vector[flavor_idx]
        
        if modifier in self.categories:
            return self.categories[modifier](flavor_value)
        else:
            return 0.0
    
    def es_formula_valida(self, expresion: str) -> bool:
        permitidos = {
            "nada_dulce", "poco_dulce", "medio_dulce", "mucho_dulce",
            "nada_amargo", "poco_amargo", "medio_amargo", "mucho_amargo",
            "nada_salado", "poco_salado", "medio_salado", "mucho_salado",
            "nada_ácido", "poco_ácido", "medio_ácido", "mucho_ácido",
            "nada_picante", "poco_picante", "medio_picante", "mucho_picante",
            "AND", "OR"
        }

        tokens = expresion.strip().split()
        if not tokens:
            return False
        return all(token in permitidos for token in tokens)

    async def handle(self, message: str) -> list[(str, int)]:
        """
        Recomienda cócteles basados en la fórmula lógica.
        Args:
            message: dict con keys:
                - content: str (fórmula lógica)
                - amount: int (cantidad de resultados)
        Returns:
            list[(str, int)]: Lista de tuplas (nombre, valor) ordenadas descendente
        """

        if message["content"]["flavors"] == "" or message["content"]["flavors"] is None:
            await self.send("validator", {"source": "flavor", "results": [], "type": "result"})
            return

        if (not self.es_formula_valida(message["content"]["flavors"])):
            await self.send("validator", {"source": "flavor", "results": [], "type": "result"})
            return

        response = []
        message_dnf = self.query_to_dnf(message["content"]["flavors"])

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
                response.append((cocktail, max_value))

        probs = softmax(response)
        drinks = select_k_without_replace(probs, message["content"]["ammount"])

        # response.sort(key=lambda x: x[1], reverse=True)
        # drinks = response[:message["content"]["ammount"]]
        filtered_results = []
        for drink in drinks:
            filtered_results.append(drink[0])
        results = self.ontology_fn(filtered_results, [[True,True,True,True,True,True,True,True,True]*len(filtered_results)], self.onto)
        filtered_results = []
        for result in results:
            if "Error" not in result:
                filtered_results.append(result)
        await self.send("validator", {"source": "flavor", "results": filtered_results, "type": "result"})