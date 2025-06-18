import random

def generar_ground_truth(flavor_vectors, formulas, agent):
    truth = {}
    for formula in formulas:
        resultados = []
        dnf = agent.query_to_dnf(formula)
        for name, vector in flavor_vectors.items():
            cumple = False
            for clause in agent.get_clauses(dnf):
                if all(agent.evaluate_term(t, vector) >= 0.7 for t in agent.get_terms(clause)):
                    cumple = True
                    break
            if cumple:
                resultados.append(name)
        truth[formula] = set(resultados)
    return truth

def run_flavor(agent, formulas, flavor_vectors, k=5):
    gt = generar_ground_truth(flavor_vectors, formulas, agent)
    resultados = []

    for formula in formulas:
        message = {"content": {"flavors": formula, "ammount": k}}
        message_dnf = agent.query_to_dnf(formula)

        recomendados = []
        for name, vector in flavor_vectors.items():
            max_val = 0.0
            for clause in agent.get_clauses(message_dnf):
                min_val = 1.0
                for term in agent.get_terms(clause):
                    min_val = min(min_val, agent.evaluate_term(term, vector))
                max_val = max(max_val, min_val)
            if max_val >= 0.7:
                recomendados.append((name, max_val))

        recomendados = [d[0] for d in sorted(recomendados, key=lambda x: x[1], reverse=True)[:k]]
        truth = gt[formula]
        hits = sum(1 for r in recomendados if r in truth)

        precision = hits / k
        recall = hits / len(truth) if truth else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

        resultados.append((formula, precision, recall, f1))

    total = len(resultados)
    avg_precision = sum(r[1] for r in resultados) / total
    avg_recall = sum(r[2] for r in resultados) / total
    avg_f1 = sum(r[3] for r in resultados) / total
    coverage = sum(1 for r in resultados if r[1] > 0) / total

    print("\n🔬 Evaluación del Flavor_Agent:")
    print(f"📊 Precision@{k}: {avg_precision:.2%}")
    print(f"📚 Recall@{k}: {avg_recall:.2%}")
    print(f"🎯 F1-score: {avg_f1:.2%}")
    print(f"📈 Cobertura: {coverage:.2%}")


def generar_formulas(n=20):
    sabores = ["dulce", "salado", "amargo", "ácido", "picante"]
    modificadores = ["nada", "poco", "medio", "muy"]
    operadores = ["AND", "OR"]

    formulas = []
    for _ in range(n):
        sabor1, sabor2 = random.sample(sabores, 2)  # sabores diferentes
        mod1 = random.choice(modificadores)
        mod2 = random.choice(modificadores)
        s1 = f"{mod1}_{sabor1}"
        s2 = f"{mod2}_{sabor2}"
        op = random.choice(operadores)
        formulas.append(f"{s1} {op} {s2}")
    return formulas
