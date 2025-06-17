import json
from sympy import to_dnf, And, Or
from agents.base_agent import BaseAgent
import numpy as np

class Flavor_Agent(BaseAgent):
    def __init__(self, name, system):
        super().__init__(name, system)

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

    async def handle(self, message: str) -> list[(str, int)]:
        """
        Recomienda cócteles basados en la fórmula lógica.
        Args:
            message: dict con keys:
                - content: str (fórmula lógica)
                - accuracy_level: float (umbral de pertenencia)
                - amount: int (cantidad de resultados)
        Returns:
            list[(str, int)]: Lista de tuplas (nombre, valor) ordenadas descendente
        """
        response = []
        message_dnf = self.query_to_dnf(message["content"])

        for cocktail in self.data:
            cocktail_vector = self.data[cocktail]
            max_value = 0.0  

            for clause in self.get_clauses(message_dnf):
                min_value = 1.0  
                
                for term in self.get_terms(clause):
                    term_value = self.evaluate_term(term, cocktail_vector)
                    min_value = min(min_value, term_value)
                
                max_value = max(max_value, min_value)

            if max_value >= message["accuracy_level"]:
                response.append((cocktail, max_value))

        response.sort(key=lambda x: x[1], reverse=True)
        return response[:message["amount"]]
                  
